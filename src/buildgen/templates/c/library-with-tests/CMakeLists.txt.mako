<%!
from buildgen.common import versions as V
%>\
cmake_minimum_required(VERSION ${V.CMAKE["min"]}...${V.CMAKE["policy_max"]})
project(${name} VERSION 1.0.0 LANGUAGES C)

set(CMAKE_C_STANDARD ${defaults.get("c_standard", V.STANDARDS["c"])})
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Library
add_library(${name} STATIC src/lib.c)
add_library(${name}::${name} ALIAS ${name})

target_include_directories(${name} PUBLIC
    $<BUILD_INTERFACE:${"$"}{CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

target_compile_options(${name} PRIVATE -Wall -Wextra)

# Tests
enable_testing()

add_executable(${name}_tests tests/test_main.c)
target_link_libraries(${name}_tests PRIVATE ${name})
target_compile_options(${name}_tests PRIVATE -Wall -Wextra)

add_test(NAME ${name}_tests COMMAND ${name}_tests)

# Install
include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

install(TARGETS ${name}
    EXPORT ${name}Targets
    ARCHIVE DESTINATION ${"$"}{CMAKE_INSTALL_LIBDIR}
    LIBRARY DESTINATION ${"$"}{CMAKE_INSTALL_LIBDIR}
)
install(DIRECTORY include/ DESTINATION ${"$"}{CMAKE_INSTALL_INCLUDEDIR})

install(EXPORT ${name}Targets
    FILE ${name}Config.cmake
    NAMESPACE ${name}::
    DESTINATION ${"$"}{CMAKE_INSTALL_LIBDIR}/cmake/${name}
)
write_basic_package_version_file(
    ${"$"}{CMAKE_CURRENT_BINARY_DIR}/${name}ConfigVersion.cmake
    VERSION ${"$"}{PROJECT_VERSION}
    COMPATIBILITY SameMajorVersion
)
install(FILES ${"$"}{CMAKE_CURRENT_BINARY_DIR}/${name}ConfigVersion.cmake
    DESTINATION ${"$"}{CMAKE_INSTALL_LIBDIR}/cmake/${name}
)
