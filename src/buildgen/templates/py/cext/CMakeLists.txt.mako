<%!
from buildgen.common import versions as V
%>\
cmake_minimum_required(VERSION ${V.CMAKE["python_ext_min"]}...${V.CMAKE["policy_max"]})
project(${"$"}{SKBUILD_PROJECT_NAME} VERSION ${"$"}{SKBUILD_PROJECT_VERSION} LANGUAGES C)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)

python_add_library(_core MODULE src/${name}/_core.c WITH_SOABI)

if(MSVC)
    target_compile_options(_core PRIVATE /W4)
else()
    target_compile_options(_core PRIVATE -Wall -Wextra)
endif()

install(TARGETS _core DESTINATION ${name})
