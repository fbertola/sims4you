from distutils import msvccompiler


def compile_cpp():
    compiler = msvccompiler.MSVCCompiler()
    compiler.initialize()
    compiler.compile(["inject_python.cpp"])
    compiler.link_executable(["inject_python.obj"], "inject_python")


if __name__ == "__main__":
    compile_cpp()
