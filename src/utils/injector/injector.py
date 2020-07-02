import os
from pathlib import Path
import subprocess

from loguru import logger


def inject(pid, file_name, exe_path=""):
    if exe_path == "":
        exe_path = Path(os.path.dirname(__file__)) / "bin" / "inject_python.exe"
    file_name = Path(file_name)

    if file_name.exists():
        with file_name.open() as code_file:
            logger.debug(f"Reading content of '{file_name}'...")

            code = code_file.read().replace('"', '\\"')

            logger.debug(f"Code string:\n\n{code}\n\n")
            logger.debug(f"Calling '{exe_path}' for PID {pid} ")

            p = subprocess.Popen(
                f'{exe_path} {pid} "{code}"',
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            out, err = p.communicate()

            logger.debug(f"STDOUT:\n{out}")
            logger.debug(f"STDERR:\n{err}")
            return p.returncode == 0
    else:
        logger.error(f"File does not exists: {file_name}")
        return False
