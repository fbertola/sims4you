import pickle
import socket
import struct
import pprint


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


if __name__ == "__main__":
    message = {
        "first_name": "ProvaUno",  # FIXME: should be configurable
        "last_name": "EGiaUnFail",  # FIXME: should be configurable
    }

    with Client(("127.0.0.1", 9000)) as client:
        response = client.send([message])

    pretty_json = pprint.pformat(response)
    print(pretty_json)
