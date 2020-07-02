import itertools

from protocolbuffers import PersistenceBlobs_pb2
from server_commands.argument_helpers import get_optional_target, OptionalSimInfoParam


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
