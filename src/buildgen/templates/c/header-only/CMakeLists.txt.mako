<%!
from buildgen.common import versions as V
%>\
cmake_minimum_required(VERSION ${V.CMAKE["min"]}...${V.CMAKE["policy_max"]})
project(${name} VERSION 1.0.0 LANGUAGES C)

add_library(${name} INTERFACE)
add_library(${name}::${name} ALIAS ${name})

target_compile_features(${name} INTERFACE c_std_${defaults.get("c_standard", V.STANDARDS["c"])})

target_include_directories(${name} INTERFACE
    $<BUILD_INTERFACE:${"$"}{CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

install(TARGETS ${name}
    EXPORT ${name}Targets
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
