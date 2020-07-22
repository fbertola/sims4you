import itertools
import json
import socket
import socketserver
import struct

from protocolbuffers import PersistenceBlobs_pb2
from server_commands.argument_helpers import get_optional_target, OptionalSimInfoParam


class IPCError(Exception):
    pass


class UnknownMessageClass(IPCError):
    pass


class InvalidSerialization(IPCError):
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
    return Message.deserialize(json.loads(data))


def _recursive_subclasses(cls):
    classmap = {}
    for subcls in cls.__subclasses__():
        classmap[subcls.__name__] = subcls
        classmap.update(_recursive_subclasses(subcls))
    return classmap


class Message(object):
    @classmethod
    def deserialize(cls, objects):
        classmap = _recursive_subclasses(cls)
        serialized = []
        for obj in objects:
            if isinstance(obj, Message):
                serialized.append(obj)
            else:
                try:
                    serialized.append(
                        classmap[obj["class"]](*obj["args"], **obj["kwargs"])
                    )
                except KeyError as e:
                    raise UnknownMessageClass(e)
                except TypeError as e:
                    raise InvalidSerialization(e)
        return serialized

    def serialize(self):
        args, kwargs = self._get_args()
        return {"class": type(self).__name__, "args": args, "kwargs": kwargs}

    def _get_args(self):
        return [], {}

    def __repr__(self):
        r = self.serialize()
        args = ", ".join([repr(arg) for arg in r["args"]])
        kwargs = "".join([", {}={}".format(k, repr(v)) for k, v in r["kwargs"].items()])
        name = r["class"]
        return "{}({}{})".format(name, args, kwargs)


class Server(socketserver.ThreadingTCPServer):
    def __init__(self, server_address, callback, bind_and_activate=True):
        if not callable(callback):
            callback = lambda x: []

        class IPCHandler(socketserver.BaseRequestHandler):
            def handle(self):
                while True:
                    try:
                        results = read_objects(self.request)
                    except ConnectionClosed as e:
                        return
                    _write_objects(self.request, callback(results))

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

    print(str(facial_attributes.sculpts))
    for modifier in itertools.chain(
        facial_attributes.face_modifiers, facial_attributes.body_modifiers
    ):
        print(str(modifier.key))

    sim_info.facial_attributes = facial_attributes.SerializeToString()
    return True
