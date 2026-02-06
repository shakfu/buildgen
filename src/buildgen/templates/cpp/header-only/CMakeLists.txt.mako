cmake_minimum_required(VERSION 3.16...3.31)
project(${name} VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD ${defaults.get("cxx_standard", 17)})
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(${name} INTERFACE)

target_include_directories(${name} INTERFACE
    $<BUILD_INTERFACE:${"$"}{CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

install(TARGETS ${name}
    EXPORT ${name}Targets
)
install(DIRECTORY include/ DESTINATION include)
install(EXPORT ${name}Targets
    FILE ${name}Config.cmake
    DESTINATION lib/cmake/${name}
)
