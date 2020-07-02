import os
import subprocess
import sys
import tempfile
import textwrap
import time


class TestProgram:
    def __init__(self, threads=1):
        self.pid = None
        _, self.temp_file = tempfile.mkstemp()

        self.script = textwrap.dedent(
            f"""
            import os, time, threading
            running = True
            pidfile = '{self.temp_file}'
            def cpu_bound():
                i = 0
                while running:
                    i += 1
        """
        )

        # CPU-bound threads
        for _ in range(threads):
            self.script += "threading.Thread(target=cpu_bound).start()\n"

        self.script += textwrap.dedent(
            """
            while os.path.exists(pidfile):
                time.sleep(0.1)
            running = False
        """
        )

    def run(self):
        p = subprocess.Popen(
            [sys.executable, "-c", self.script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        i = 0
        while not os.path.exists(self.temp_file):
            time.sleep(0.1)
            i += 1
            if i > 100:
                raise Exception("Program never touched pid file!")
        return p

    def stop(self):
        os.unlink(self.temp_file)
