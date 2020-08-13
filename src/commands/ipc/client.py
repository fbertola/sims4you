import json
import socket
import struct

from src.imitator_mod.scripts.randomize_facial_attributes import Message, read_objects


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
        return read_objects(self.sock)

    def _write_objects(self, sock, objects):
        data = json.dumps(list((o.get_payload() for o in objects)))
        sock.sendall(struct.pack("!i", len(data) + 4))
        sock.sendall(data.encode())


if __name__ == "__main__":
    with Client(("127.0.0.1", 9000)) as client:
        response = client.send([Message("Hello")])
    print("Received objects: {}".format(response))
