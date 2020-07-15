from distutils.spawn import find_executable
import os
import sys

import click
from pygdbmi.gdbcontroller import GdbController


def _check_if_python_process(json_out):
    return any(
        "PyRun_SimpleString" in key["payload"]
        for key in json_out
        if key["type"] == "result" and key["payload"]
    )


@click.command()
@click.argument("pid")
@click.argument("filename")
def inject(pid, filename):
    filename = os.path.abspath(filename)
    dirname = os.path.dirname(filename)

    if sys.platform == "win32":
        filename = filename.replace("\\", "/")
        dirname = dirname.replace("\\", "/")

    if not find_executable("gdb"):
        click.echo(click.style("gdb executable could not be resolved", fg="red"))
        exit(1)

    gdb_controller = GdbController()

    click.echo(click.style(f"Attaching gdb to PID {pid}", fg="green"))
    gdb_controller.write(f"attach {pid}")

    click.echo(click.style("Checking if Python functions are defined", fg="green"))
    defined_functions = gdb_controller.write("info functions PyRun_SimpleString")

    if not _check_if_python_process(defined_functions):
        click.echo(
            click.style(
                "Python functions are not defined in the attached process!", fg="red"
            )
        )
        exit(1)

    click.echo(click.style("Injecting Python code", fg="green"))
    gdb_controller.write("call (int)PyGILState_Ensure()")
    gdb_controller.write(
        f'call (int)PyRun_SimpleString("import sys; sys.path.insert(0, \\"{dirname}\\"); exec(open(\\"{filename}\\").read())")'
    )
    gdb_controller.write("call (int)PyGILState_Release($1)")

    click.echo(click.style(f"Detaching from {pid}", fg="green"))
    gdb_controller.write("set confirm off")
    gdb_controller.write("quit")
    gdb_controller.exit()
