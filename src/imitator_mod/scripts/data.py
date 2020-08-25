import json

from pathlib import Path

json_dir = Path(__file__).parent

# FIXME: read from zipfile if inside TS4
with open(json_dir / "face_modifiers.json") as fp:
    face_modifiers = json.load(fp)

with open(json_dir / "facial_sculpts.json") as fp:
    facial_sculpts = json.load(fp)

with open(json_dir / "facial_casps.json") as fp:
    facial_casps = json.load(fp)
