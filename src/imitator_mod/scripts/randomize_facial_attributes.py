import atexit
import itertools
import json
import socket
import socketserver
import struct
import threading

from protocolbuffers import PersistenceBlobs_pb2
from server_commands.argument_helpers import get_optional_target, OptionalSimInfoParam


class IPCError(Exception):
    pass


class ConnectionClosed(IPCError):
    pass


def read_objects(sock):
    header = sock.recv(4)
    if len(header) == 0:
        raise ConnectionClosed()
    size = struct.unpack("!i", header)[0]
    data = sock.recv(size - 4)
    if len(data) == 0:
        raise ConnectionClosed()
    return list((Message(o) for o in json.loads(data)))


def write_objects(sock, objects):
    data = json.dumps(list((o.get_payload() for o in objects)))
    sock.sendall(struct.pack("!i", len(data) + 4))
    sock.sendall(data.encode())


class Message(object):
    def __init__(self, payload):
        self.payload = payload

    def get_payload(self):
        return self.payload


class Server(socketserver.ThreadingTCPServer):
    def __init__(self, server_address, callback=None, bind_and_activate=True):
        if not callable(callback):
            callback = lambda x: [Message(payload=randomize_facial_attributes())]

        class IPCHandler(socketserver.BaseRequestHandler):
            def handle(self):
                while True:
                    try:
                        results = read_objects(self.request)
                    except ConnectionClosed as e:
                        return
                    write_objects(self.request, callback(results))

            self.address_family = socket.AF_INET

        socketserver.TCPServer.__init__(
            self, server_address, IPCHandler, bind_and_activate
        )


def randomize_facial_attributes():
    sim_info = get_optional_target(
        None, target_type=OptionalSimInfoParam, _connection=None
    )
    if sim_info is None:
        print("sim_info is None")
        return False

    facial_attributes = PersistenceBlobs_pb2.BlobSimFacialCustomizationData()
    facial_attributes.MergeFromString(sim_info.facial_attributes)

    payload = {"sculpts": str(facial_attributes.sculpts)}

    for modifier in itertools.chain(
            facial_attributes.face_modifiers, facial_attributes.body_modifiers
    ):
        payload[str(modifier.key)] = str(modifier.value)

    sim_info.facial_attributes = facial_attributes.SerializeToString()
    return payload


server = Server(("127.0.0.1", 9000))
server_thread = threading.Thread(target=server.serve_forever)
server_thread.daemon = True
server_thread.start()

atexit.register(server.server_close)
atexit.register(server.shutdown)
