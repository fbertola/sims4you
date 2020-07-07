import os
from pathlib import Path
import subprocess

from loguru import logger
from pygdbmi.gdbcontroller import GdbController


def inject(pid, filename):
    filename = os.path.abspath(filename)

    gdb_controller = GdbController()
    print(gdb_controller.write(f"attach {pid}"))
    print(gdb_controller.write("call (int)PyGILState_Ensure()"))
    # print(gdb_controller.write(f"call (int)PyRun_SimpleString(\"import sys; sys.path.insert(0, r\\\"{os.path.dirname(filename)}\\\"); sys.path.insert(0, r\\\"{os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))}\\\");  exec(open(\\\"{filename}\\\").read())\")"))
    print(gdb_controller.write(f"call (int)PyRun_SimpleString(\"print(1)\")"))
    print(gdb_controller.write("call (int)PyGILState_Release($1)"))
    gdb_controller.exit()

