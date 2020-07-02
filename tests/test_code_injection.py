from tests.utils import TestProgram


def assert_output_contains(stdout, stderr, text):
    assert text in str(
        stdout
    ), f"Code injection failed: {str(stdout)}\n{str(stderr)}"


def test_injection():
    p = None

    try:
        program = TestProgram()
        p = program.run()
        # inject(p.pid, "pyrasite/payloads/helloworld.py")
        program.stop()
        stdout, stderr = p.communicate()
        assert_output_contains(stdout, stderr, "Hello World!")
    finally:
        if p:
            p.kill()
