cmake_minimum_required(VERSION 3.16...3.31)
project(${name} VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD ${defaults.get("cxx_standard", 17)})
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Internal library
add_library(${name}_lib STATIC src/lib.cpp)

target_include_directories(${name}_lib PUBLIC
    $<BUILD_INTERFACE:${"$"}{CMAKE_CURRENT_SOURCE_DIR}/include>
)

target_compile_options(${name}_lib PRIVATE -Wall -Wextra)

# Executable
add_executable(${name} src/main.cpp)
target_link_libraries(${name} PRIVATE ${name}_lib)
target_compile_options(${name} PRIVATE -Wall -Wextra)

install(TARGETS ${name} RUNTIME DESTINATION bin)
