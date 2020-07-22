import fnmatch
import os
from zipfile import PyZipFile, ZIP_STORED

import shutil

import io
from Utilities.unpyc3 import decompile
import fnmatch
import os


def decompile_dir(rootPath):
    pattern = "*.pyc"
    for root, dirs, files in os.walk(rootPath):
        for filename in fnmatch.filter(files, pattern):
            p = str(os.path.join(root, filename))
            try:
                py = decompile(p)
                with io.open(
                    p.replace(".pyc", ".py"), "w", encoding="utf-8"
                ) as output_py:
                    for statement in py.statements:
                        output_py.write(str(statement) + "\r")
                print(p)
            except Exception as ex:
                print("FAILED to decompile %s" % p)


script_package_types = ["*.zip", "*.ts4script"]


def extract_subfolder(root, filename, ea_folder):
    src = os.path.join(root, filename)
    dst = os.path.join(ea_folder, filename)
    if src != dst:
        shutil.copyfile(src, dst)
    zip = PyZipFile(dst)
    out_folder = os.path.join(ea_folder, os.path.splitext(filename)[0])
    zip.extractall(out_folder)
    decompile_dir(out_folder)
    pass


def extract_folder(ea_folder, gameplay_folder):
    for root, dirs, files in os.walk(gameplay_folder):
        for ext_filter in script_package_types:
            for filename in fnmatch.filter(files, ext_filter):
                extract_subfolder(root, filename, ea_folder)
