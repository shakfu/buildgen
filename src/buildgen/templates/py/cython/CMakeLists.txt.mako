cmake_minimum_required(VERSION 3.15...3.30)
project(${"$"}{SKBUILD_PROJECT_NAME} VERSION ${"$"}{SKBUILD_PROJECT_VERSION} LANGUAGES C)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(Cython REQUIRED)

cython_transpile(src/${name}/_core.pyx LANGUAGE C OUTPUT_VARIABLE _core_c)

python_add_library(_core MODULE ${"$"}{_core_c} WITH_SOABI)

install(TARGETS _core DESTINATION ${name})
