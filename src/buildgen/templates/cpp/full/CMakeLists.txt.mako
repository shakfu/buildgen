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

# Library
add_library(${name}_lib STATIC src/lib.cpp)

target_include_directories(${name}_lib PUBLIC
    $<BUILD_INTERFACE:${"$"}{CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

target_compile_options(${name}_lib PRIVATE ${"$"}{WARNING_FLAGS})

# Executable
add_executable(${name} src/main.cpp)
target_link_libraries(${name} PRIVATE ${name}_lib)
target_compile_options(${name} PRIVATE ${"$"}{WARNING_FLAGS})

# Tests
enable_testing()

add_executable(${name}_tests tests/test_main.cpp)
target_link_libraries(${name}_tests PRIVATE ${name}_lib)
target_compile_options(${name}_tests PRIVATE ${"$"}{WARNING_FLAGS})

add_test(NAME ${name}_tests COMMAND ${name}_tests)

# Install
install(TARGETS ${name}_lib
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)
install(TARGETS ${name} RUNTIME DESTINATION bin)
install(DIRECTORY include/ DESTINATION include)
