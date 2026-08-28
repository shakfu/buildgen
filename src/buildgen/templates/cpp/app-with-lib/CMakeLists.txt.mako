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

# Internal library
add_library(${name}_lib STATIC src/lib.cpp)

target_include_directories(${name}_lib PUBLIC
    $<BUILD_INTERFACE:${"$"}{CMAKE_CURRENT_SOURCE_DIR}/include>
)

target_compile_options(${name}_lib PRIVATE ${"$"}{WARNING_FLAGS})

# Executable
add_executable(${name} src/main.cpp)
target_link_libraries(${name} PRIVATE ${name}_lib)
target_compile_options(${name} PRIVATE ${"$"}{WARNING_FLAGS})

install(TARGETS ${name} RUNTIME DESTINATION bin)
