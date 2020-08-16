import atexit
import itertools
import json
import socket
import socketserver
import struct
import sys
import traceback

import services
from protocolbuffers import PersistenceBlobs_pb2
from server_commands.argument_helpers import get_optional_target, OptionalSimInfoParam
import threading


def read_objects(sock):
    header = sock.recv(4)
    if len(header) == 0:
        raise ConnectionError()
    size = struct.unpack("!i", header)[0]
    data = sock.recv(size - 4)
    if len(data) == 0:
        raise ConnectionError()
    return json.loads(data)


def write_objects(sock, objects):
    data = json.dumps(objects)
    sock.sendall(struct.pack("!i", len(data) + 4))
    sock.sendall(data.encode())


class Server(socketserver.ThreadingTCPServer):
    def __init__(self, server_address, callback=None, bind_and_activate=True):
        if not callable(callback):
            callback = lambda x: [randomize_facial_attributes(o) for o in x]

        class IPCHandler(socketserver.BaseRequestHandler):
            def handle(self):
                while True:
                    try:
                        results = read_objects(self.request)
                    except ConnectionError as e:
                        return
                    write_objects(self.request, callback(results))

            self.address_family = socket.AF_INET

        socketserver.TCPServer.__init__(
            self, server_address, IPCHandler, bind_and_activate
        )


def randomize_facial_attributes(params):
    try:
        first_name = params["first_name"]
        last_name = params["last_name"]
        sim_id = 0
        info = services.sim_info_manager().get_sim_info_by_name(first_name, last_name)
        if info is not None:
            sim_id = info.id

        sim_info = get_optional_target(
            OptionalSimInfoParam(str(sim_id)), target_type=OptionalSimInfoParam, _connection=None
        )
        if sim_info is None:
            return {"error": "SimInfo is None"}

        facial_attributes = PersistenceBlobs_pb2.BlobSimFacialCustomizationData()
        facial_attributes.MergeFromString(sim_info.facial_attributes)

        payload = {"sculpts": str(sim_info.facial_attributes)}

        for modifier in itertools.chain(
            facial_attributes.face_modifiers, facial_attributes.body_modifiers
        ):
            payload[str(modifier.key)] = str(modifier.amount)

        sim_info.facial_attributes = facial_attributes.SerializeToString()
        return payload
    except Exception as e:
        exc_info = sys.exc_info()
        return {"exception": ''.join(traceback.format_exception(*exc_info))}


server = Server(("127.0.0.1", 9000))
server_thread = threading.Thread(target=server.serve_forever)
server_thread.daemon = True
server_thread.start()

atexit.register(server.server_close)
atexit.register(server.shutdown)

