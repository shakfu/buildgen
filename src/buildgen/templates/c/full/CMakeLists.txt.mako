<%!
from buildgen.common import versions as V
%>\
cmake_minimum_required(VERSION ${V.CMAKE["min"]}...${V.CMAKE["policy_max"]})
project(${name} VERSION 1.0.0 LANGUAGES C)

set(CMAKE_C_STANDARD ${defaults.get("c_standard", V.STANDARDS["c"])})
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Library
add_library(${name}_lib STATIC src/lib.c)

target_include_directories(${name}_lib PUBLIC
    $<BUILD_INTERFACE:${"$"}{CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

target_compile_options(${name}_lib PRIVATE -Wall -Wextra)

# Executable
add_executable(${name} src/main.c)
target_link_libraries(${name} PRIVATE ${name}_lib)
target_compile_options(${name} PRIVATE -Wall -Wextra)

# Tests
enable_testing()

add_executable(${name}_tests tests/test_main.c)
target_link_libraries(${name}_tests PRIVATE ${name}_lib)
target_compile_options(${name}_tests PRIVATE -Wall -Wextra)

add_test(NAME ${name}_tests COMMAND ${name}_tests)

# Install
install(TARGETS ${name}_lib
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)
install(TARGETS ${name} RUNTIME DESTINATION bin)
install(DIRECTORY include/ DESTINATION include)
