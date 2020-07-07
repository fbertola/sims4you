import subprocess
import sys
import tempfile
import textwrap


class TestProgram:
    def __init__(self):
        self.pid = None
        fd, self.filename = tempfile.mkstemp()
        tmp_file = open(fd, 'w')
        self.script = textwrap.dedent(
            f"""
            import time
            while True:
                time.sleep(0.1)
        """
        )
        tmp_file.write(self.script)
        tmp_file.close()

    def run(self):
        self.process = subprocess.Popen(
            f"{sys.executable} {self.filename}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        return self.process

    def stop(self):
        self.process.kill()
