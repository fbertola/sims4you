import atexit
import pickle
import random
import socket
import socketserver
import struct
import sys
import traceback

import services
from protocolbuffers import PersistenceBlobs_pb2, Outfits_pb2
from server_commands.argument_helpers import get_optional_target, OptionalSimInfoParam
import threading

from Scripts.data import *


def read_objects(sock):
    header = sock.recv(4)
    if len(header) == 0:
        raise ConnectionError()
    size = struct.unpack("!i", header)[0]
    data = sock.recv(size - 4)
    if len(data) == 0:
        raise ConnectionError()
    return pickle.loads(data)


def write_objects(sock, objects):
    try:
        data = pickle.dumps(objects)
    except Exception as e:
        exc_info = sys.exc_info()
        data = {"exception": "".join(traceback.format_exception(*exc_info))}

    sock.sendall(struct.pack("!i", len(data) + 4))
    sock.sendall(data)


class Server(socketserver.ThreadingTCPServer):
    def __init__(self, server_address, callback=None, bind_and_activate=True):
        if not callable(callback):
            callback = lambda x: [randomize_sim(o) for o in x]

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
        region = v["region"]
        ages = v["age"]
        genders = v["gender"]

        # FIXME: should be configurable
        if ("Male" not in genders and "Unisex" not in genders) or "Adult" not in ages:
            continue

        if region in sculpt_buckets:
            sculpt_buckets[region].append(k)
        else:
            sculpt_buckets[region] = [k]

    return sculpt_buckets


def override_casps(current_outfit, casps):
    other_casps = []
    casps_ext_dict = {}
    for casp in list(current_outfit.parts.ids):
        if str(casp) in facial_casps:
            casps_ext_dict[facial_casps[str(casp)]["body_type"]] = casp
        else:
            other_casps.append(casp)
    for k, v in casps.items():
        if v == "None":
            continue

        if k in casps_ext_dict:
            casps_ext_dict[k] = v  # Override value
        else:
            other_casps.append(v)
    return list(casps_ext_dict.values()) + other_casps


def get_sim_info(first_name, last_name):
    info = services.sim_info_manager().get_sim_info_by_name(first_name, last_name)

    if info is None:
        return None

    sim_info = get_optional_target(
        OptionalSimInfoParam(str(info.id)),
        target_type=OptionalSimInfoParam,
        _connection=None,
    )

    return sim_info


def randomize_facial_attributes(params):
    try:
        first_name = params["first_name"]
        last_name = params["last_name"]

        sim_info = get_sim_info(first_name, last_name)

        if sim_info is None:
            return {"error": f"cannot find Sim {first_name} {last_name}"}

        facial_attributes = PersistenceBlobs_pb2.BlobSimFacialCustomizationData()
        facial_attributes.MergeFromString(sim_info.facial_attributes)

        payload = {
            "face_mods": {},
        }

        face_modifiers = []

        for k, v in facial_modifiers.items():
            ages = v["age"]
            genders = v["gender"]

            # FIXME: this should be configurable
            if ("Male" not in genders and "Unisex" not in genders) or "Adult" not in ages:
                continue

            amount = random.random()
            payload["face_mods"][k] = amount
            modifier = PersistenceBlobs_pb2.BlobSimFacialCustomizationData.Modifier()
            modifier.key = int(v)
            modifier.amount = random.random()
            face_modifiers.append(modifier)

        del facial_attributes.face_modifiers[:]
        facial_attributes.face_modifiers.extend(face_modifiers)
        # TODO: body modifiers?

        sim_info.facial_attributes = facial_attributes.SerializeToString()
        sim_info.resend_physical_attributes()

        return payload

    except Exception as e:
        exc_info = sys.exc_info()
        return {"exception": "".join(traceback.format_exception(*exc_info))}


def randomize_facial_sculpts(params):
    try:
        first_name = params["first_name"]
        last_name = params["last_name"]
        randomized_sculpts = (
            random.choice(v) for k, v in create_sculpt_buckets().items()
        )
        sim_info = get_sim_info(first_name, last_name)

        if sim_info is None:
            return {"error": f"cannot find Sim {first_name} {last_name}"}

        facial_attributes = PersistenceBlobs_pb2.BlobSimFacialCustomizationData()
        facial_attributes.MergeFromString(sim_info.facial_attributes)

        payload = {
            "sculpts": list((int(s) for s in randomized_sculpts)),
        }

        facial_attributes.sculpts[:] = payload["sculpts"]

        sim_info.facial_attributes = facial_attributes.SerializeToString()
        sim_info.resend_physical_attributes()

        return payload

    except Exception as e:
        exc_info = sys.exc_info()
        return {"exception": "".join(traceback.format_exception(*exc_info))}


def randomize_facial_casps(params):
    try:
        first_name = params["first_name"]
        last_name = params["last_name"]
        randomized_casps = {
            k: random.choice(v) for k, v in create_casp_buckets().items()
        }
        sim_info = get_sim_info(first_name, last_name)

        if sim_info is None:
            return {"error": f"cannot find Sim {first_name} {last_name}"}

        sim_proto = services.get_persistence_service().get_sim_proto_buff(
            sim_info.sim_id
        )

        if sim_proto is None:
            return {"error": "Cannot get SimInfo ProtoBuf object"}

        current_outfit = list(sim_proto.outfits.outfits)[sim_proto.current_outfit_index]

        payload = {"casps": dict(randomized_casps)}

        casps = override_casps(current_outfit, payload["casps"])
        current_outfit.parts.ids[:] = list(int(c) for c in casps)

        sim_info.resend_physical_attributes()

        return payload

    except Exception as e:
        exc_info = sys.exc_info()
        return {"exception": "".join(traceback.format_exception(*exc_info))}


def randomize_sim(params):
    first_pass = randomize_facial_sculpts(params)

    if "sculpts" in first_pass:
        params["sculpts"] = first_pass["sculpts"]

    second_pass = (randomize_facial_attributes(params),)
    # third_pass = randomize_facial_casps(params),

    return [
        first_pass,
        second_pass,
    ]


server = Server(("127.0.0.1", 9000))
server_thread = threading.Thread(target=server.serve_forever)
server_thread.daemon = True
server_thread.start()

atexit.register(server.server_close)
atexit.register(server.shutdown)
