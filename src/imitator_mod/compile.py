import os
import shutil
from zipfile import PyZipFile, ZIP_STORED

import settings


def compile_module(creator_name, ea_root, mods_folder, mod_name=None, copy_to_mod_folder=True):
    src = os.path.join(ea_root, "Scripts")
    if not mod_name:
        mod_name = os.path.basename(
            os.path.normpath(os.path.dirname(os.path.realpath("__file__")))
        )

    mod_name = creator_name + "_" + mod_name
    ts4script = os.path.join(ea_root, mod_name + ".ts4script")

    ts4script_mods = os.path.join(os.path.join(mods_folder), mod_name + ".ts4script")

    zf = PyZipFile(
        ts4script, mode="w", compression=ZIP_STORED, allowZip64=True, optimize=2
    )
    for folder, subs, files in os.walk(src):
        zf.writepy(folder)
    zf.close()

    if copy_to_mod_folder:
        shutil.copyfile(ts4script, ts4script_mods)


if __name__ == "__main__":
    root = os.path.dirname(os.path.realpath("__file__"))
    compile_module(settings.creator_name, root, settings.mods_folder)
