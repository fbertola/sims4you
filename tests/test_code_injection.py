from click.testing import CliRunner

from src.commands.inject.inject import inject
from tests.utils import TestProgram


def assert_output_contains(stdout, stderr, text):
    assert text in str(stdout), f"Code injection failed: {str(stdout)}\n{str(stderr)}"


def test_injection():
    p = None
    runner = CliRunner()

    try:
        program = TestProgram()
        p = program.run()
        result = runner.invoke(inject, (str(p.pid), "./scripts/hello.py"))
        program.stop()
        print(result.output)
    finally:
        if p:
            p.kill()
