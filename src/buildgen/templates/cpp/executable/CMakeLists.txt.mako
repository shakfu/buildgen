<%!
from buildgen.common import versions as V
%>\
cmake_minimum_required(VERSION ${V.CMAKE["min"]}...${V.CMAKE["policy_max"]})
project(${name} VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD ${defaults.get("cxx_standard", V.STANDARDS["cxx"])})
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if(MSVC)
    set(WARNING_FLAGS /W4)
else()
    set(WARNING_FLAGS -Wall -Wextra)
endif()

add_executable(${name} src/main.cpp)

target_compile_options(${name} PRIVATE ${"$"}{WARNING_FLAGS})

install(TARGETS ${name} RUNTIME DESTINATION bin)
