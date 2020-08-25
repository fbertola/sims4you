import json
import zipfile

from pathlib import Path

json_dir = Path(__file__).parent

if json_dir.is_file():
    # Read from zip
    with zipfile.ZipFile(json_dir) as z:
        with z.open("Scripts/face_modifiers.json") as fp:
            data = fp.read()
            face_modifiers = json.loads(data.decode())

        with z.open("Scripts/facial_sculpts.json") as fp:
            data = fp.read()
            facial_sculpts = json.loads(data.decode())

        with z.open("Scripts/facial_casps.json") as fp:
            data = fp.read()
            facial_casps = json.loads(data.decode())
else:
    with open(json_dir / "face_modifiers.json") as fp:
        face_modifiers = json.load(fp)

    with open(json_dir / "facial_sculpts.json") as fp:
        facial_sculpts = json.load(fp)

    with open(json_dir / "facial_casps.json") as fp:
        facial_casps = json.load(fp)
