cmake_minimum_required(VERSION 3.15...3.30)
project(${"$"}{SKBUILD_PROJECT_NAME} VERSION ${"$"}{SKBUILD_PROJECT_VERSION} LANGUAGES C)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)

python_add_library(_core MODULE src/${name}/_core.c WITH_SOABI)

install(TARGETS _core DESTINATION ${name})
