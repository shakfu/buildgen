cmake_minimum_required(VERSION 3.15...3.30)
project(${"$"}{SKBUILD_PROJECT_NAME} VERSION ${"$"}{SKBUILD_PROJECT_VERSION} LANGUAGES C)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)

add_custom_command(
    OUTPUT _core.c
    COMMAND Python::Interpreter -m cython
        "${"$"}{CMAKE_CURRENT_SOURCE_DIR}/src/${name}/_core.pyx" --output-file _core.c
    DEPENDS src/${name}/_core.pyx
)

python_add_library(_core MODULE _core.c WITH_SOABI)

install(TARGETS _core DESTINATION ${name})
