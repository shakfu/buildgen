<%page args="name, options={}" />
<%
raw_options = locals().get("options")
if not isinstance(raw_options, dict):
    raw_options = {}
opts = raw_options
test_framework = opts.get("test_framework", "catch2")
build_examples = bool(opts.get("build_examples", False))
build_cpp_tests_default = "ON" if test_framework != "none" else "OFF"
%>

cmake_minimum_required(VERSION 3.18...3.30)
project(${"$"}{SKBUILD_PROJECT_NAME} VERSION ${"$"}{SKBUILD_PROJECT_VERSION} LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(BUILD_CPP_TESTS "Build native Catch2/GTest harness" ${build_cpp_tests_default})
if(NOT DEFINED TEST_FRAMEWORK)
    set(TEST_FRAMEWORK "${test_framework}" CACHE STRING "catch2;gtest;none")
endif()
set_property(CACHE TEST_FRAMEWORK PROPERTY STRINGS catch2 gtest none)
option(BUILD_EMBEDDED_CLI "Build C++ CLI example that embeds Python" ${"ON" if build_examples else "OFF"})

find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(_core MODULE src/${name}/_core.cpp)
target_compile_features(_core PRIVATE cxx_std_17)
install(TARGETS _core DESTINATION ${name})

if(BUILD_CPP_TESTS)
    include(CTest)
    include(FetchContent)

    if(TEST_FRAMEWORK STREQUAL "catch2")
        FetchContent_Declare(
            catch2
            GIT_REPOSITORY https://github.com/catchorg/Catch2.git
            GIT_TAG v3.5.3
        )
        FetchContent_MakeAvailable(catch2)

        add_executable(${name}_catch2 tests/native/test_module.catch2.cpp)
        target_link_libraries(${name}_catch2 PRIVATE Catch2::Catch2WithMain pybind11::embed)
        target_compile_features(${name}_catch2 PRIVATE cxx_std_17)

        include(Catch)
<%text>
        catch_discover_tests(${name}_catch2
            TEST_PREFIX "native::"
            PROPERTIES
                ENVIRONMENT "PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/src:${CMAKE_CURRENT_BINARY_DIR}/src"
        )
</%text>
    elseif(TEST_FRAMEWORK STREQUAL "gtest")
        FetchContent_Declare(
            gtest
            GIT_REPOSITORY https://github.com/google/googletest.git
            GIT_TAG v1.14.0
        )
        set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
        FetchContent_MakeAvailable(gtest)

        add_executable(${name}_gtest tests/native/test_module.gtest.cpp)
        target_link_libraries(${name}_gtest PRIVATE GTest::gtest_main pybind11::embed)
        target_compile_features(${name}_gtest PRIVATE cxx_std_17)

        include(GoogleTest)
<%text>
        gtest_discover_tests(${name}_gtest
            TEST_PREFIX "native::"
            PROPERTIES
                ENVIRONMENT "PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/src:${CMAKE_CURRENT_BINARY_DIR}/src"
        )
</%text>
    elseif(TEST_FRAMEWORK STREQUAL "none")
        message(WARNING "BUILD_CPP_TESTS requested but TEST_FRAMEWORK=none. Skipping native harness.")
    else()
        message(FATAL_ERROR "TEST_FRAMEWORK must be 'catch2', 'gtest', or 'none'")
    endif()
endif()

if(BUILD_EMBEDDED_CLI)
    add_executable(${name}_cli examples/cli/main.cpp)
    target_link_libraries(${name}_cli PRIVATE pybind11::embed)
    target_compile_features(${name}_cli PRIVATE cxx_std_17)
endif()
