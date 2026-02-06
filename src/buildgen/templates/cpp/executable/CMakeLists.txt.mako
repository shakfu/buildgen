cmake_minimum_required(VERSION 3.16...3.31)
project(${name} VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD ${defaults.get("cxx_standard", 17)})
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_executable(${name} src/main.cpp)

target_compile_options(${name} PRIVATE -Wall -Wextra)

install(TARGETS ${name} RUNTIME DESTINATION bin)
