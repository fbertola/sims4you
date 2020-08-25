import pickle
import socket
import struct
import pprint
import random

from src.imitator_mod.scripts.data import facial_casps, facial_sculpts, face_modifiers


class Client(object):
    def __init__(self, server_address):
        self.addr = server_address
        if isinstance(self.addr, str):
            address_family = socket.AF_UNIX
        else:
            address_family = socket.AF_INET
        self.sock = socket.socket(address_family, socket.SOCK_STREAM)

    def connect(self):
        self.sock.connect(self.addr)

    def close(self):
        self.sock.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def send(self, objects):
        self._write_objects(self.sock, objects)
        return self._read_objects(self.sock)

    @staticmethod
    def _write_objects(sock, objects):
        data = pickle.dumps(objects)
        sock.sendall(struct.pack("!i", len(data) + 4))
        sock.sendall(data)

    @staticmethod
    def _read_objects(sock):
        header = sock.recv(4)
        if len(header) == 0:
            raise ConnectionError()
        size = struct.unpack("!i", header)[0]
        data = sock.recv(size - 4)
        if len(data) == 0:
            raise ConnectionError()
        return pickle.loads(data)


def create_casp_buckets():
    casp_buckets = {}

    for k, v in facial_casps.items():
        body_type = v["body_type"]
        ages = v["age"]
        genders = v["gender"]

        # FIXME: should be configurable
        if ("Male" not in genders and "Unisex" not in genders) or "Adult" not in ages:
            continue

        if body_type in casp_buckets:
            casp_buckets[body_type].append(k)
        else:
            casp_buckets[body_type] = [k]

    return casp_buckets


def create_sculpt_buckets():
    sculpt_buckets = {}

    for k, v in facial_sculpts.items():
        if v in sculpt_buckets:
            sculpt_buckets[v].append(k)
        else:
            sculpt_buckets[v] = [k]

    return sculpt_buckets


if __name__ == "__main__":
    face_mods = {k: random.random() for k, _ in face_modifiers.items()}
    sculpts = (random.choice(v) for k, v in create_sculpt_buckets().items())
    casps = {k: random.choice(v) for k, v in create_casp_buckets().items()}

    message = {
        "first_name": "ProvaUno",  # FIXME: should be configurable
        "last_name": "EGiaUnFail",  # FIXME: should be configurable
        "face_mods": dict(face_mods),
        "sculpts": list((int(s) for s in sculpts)),
        "casps": dict(casps)
    }

    with Client(("127.0.0.1", 9000)) as client:
        response = client.send([message])
    pretty_json = pprint.pformat(response)
    print(pretty_json)
