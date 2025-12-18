"""Tests for CMake generation and building."""

import pytest
import tempfile
import os
from pathlib import Path

from buildgen.cmake.variables import (
    CMakeVar,
    CMakeCacheVar,
    CMakeOption,
    CMakeEnvVar,
    cmake_var,
    cmake_env_var,
    cmake_bool,
)
from buildgen.cmake.generator import CMakeListsGenerator
from buildgen.cmake.builder import CMakeBuilder
from buildgen.cmake.functions import Cm


class TestCMakeVariables:
    """Test CMake variable classes."""

    def test_cmake_var_single_value(self):
        """Test CMakeVar with single value."""
        var = CMakeVar("MY_VAR", "value")
        assert str(var) == "set(MY_VAR value)"

    def test_cmake_var_multiple_values(self):
        """Test CMakeVar with multiple values (list)."""
        var = CMakeVar("MY_LIST", "a", "b", "c")
        assert str(var) == "set(MY_LIST a b c)"

    def test_cmake_var_with_spaces(self):
        """Test CMakeVar with value containing spaces."""
        var = CMakeVar("MY_VAR", "value with spaces")
        assert str(var) == 'set(MY_VAR "value with spaces")'

    def test_cmake_var_parent_scope(self):
        """Test CMakeVar with PARENT_SCOPE."""
        var = CMakeVar("MY_VAR", "value", parent_scope=True)
        assert "PARENT_SCOPE" in str(var)

    def test_cmake_var_empty_raises(self):
        """Test that empty CMakeVar raises error."""
        with pytest.raises(ValueError):
            CMakeVar("MY_VAR")

    def test_cmake_cache_var(self):
        """Test CMakeCacheVar."""
        var = CMakeCacheVar("MY_CACHE", "value", "STRING", "Documentation")
        result = str(var)
        assert "CACHE" in result
        assert "STRING" in result
        assert "Documentation" in result

    def test_cmake_cache_var_bool(self):
        """Test CMakeCacheVar with BOOL type."""
        var = CMakeCacheVar("MY_BOOL", "ON", "BOOL", "A boolean option")
        result = str(var)
        assert "BOOL" in result

    def test_cmake_cache_var_force(self):
        """Test CMakeCacheVar with FORCE."""
        var = CMakeCacheVar("MY_VAR", "value", force=True)
        assert "FORCE" in str(var)

    def test_cmake_cache_var_invalid_type(self):
        """Test CMakeCacheVar with invalid type."""
        with pytest.raises(ValueError):
            CMakeCacheVar("MY_VAR", "value", "INVALID_TYPE")

    def test_cmake_option(self):
        """Test CMakeOption."""
        opt = CMakeOption("ENABLE_TESTS", "Enable testing", True)
        result = str(opt)
        assert "option(" in result
        assert "ENABLE_TESTS" in result
        assert "Enable testing" in result
        assert "ON" in result

    def test_cmake_option_default_off(self):
        """Test CMakeOption with default OFF."""
        opt = CMakeOption("MY_OPTION", "Description", False)
        assert "OFF" in str(opt)

    def test_cmake_env_var(self):
        """Test CMakeEnvVar."""
        env = CMakeEnvVar("PATH")
        assert str(env) == "$ENV{PATH}"

    def test_cmake_env_var_set(self):
        """Test CMakeEnvVar.set()."""
        env = CMakeEnvVar("MY_VAR")
        assert "set(ENV{MY_VAR}" in env.set("value")

    def test_cmake_var_reference(self):
        """Test cmake_var function."""
        assert cmake_var("MY_VAR") == "${MY_VAR}"

    def test_cmake_env_var_reference(self):
        """Test cmake_env_var function."""
        assert cmake_env_var("PATH") == "$ENV{PATH}"

    def test_cmake_bool(self):
        """Test cmake_bool function."""
        assert cmake_bool(True) == "ON"
        assert cmake_bool(False) == "OFF"


class TestCMakeFunctions:
    """Test CMake function helpers."""

    def test_cmake_minimum_required(self):
        """Test Cm.minimum_required."""
        result = Cm.minimum_required("3.16")
        assert "cmake_minimum_required(VERSION 3.16" in result
        assert "FATAL_ERROR" in result

    def test_cmake_minimum_required_no_fatal(self):
        """Test Cm.minimum_required without FATAL_ERROR."""
        result = Cm.minimum_required("3.16", fatal_error=False)
        assert "FATAL_ERROR" not in result

    def test_cmake_project_simple(self):
        """Test simple Cm.project."""
        result = Cm.project("MyProject")
        assert "project(MyProject)" in result

    def test_cmake_project_full(self):
        """Test Cm.project with all options."""
        result = Cm.project(
            "MyProject",
            version="1.0.0",
            description="My description",
            languages=["C", "CXX"],
        )
        assert "project(MyProject" in result
        assert "VERSION 1.0.0" in result
        assert "DESCRIPTION" in result
        assert "LANGUAGES C CXX" in result

    def test_cmake_add_executable(self):
        """Test Cm.add_executable."""
        result = Cm.add_executable("myapp", "main.cpp", "util.cpp")
        assert "add_executable(myapp main.cpp util.cpp)" in result

    def test_cmake_add_executable_win32(self):
        """Test Cm.add_executable with WIN32."""
        result = Cm.add_executable("myapp", "main.cpp", win32=True)
        assert "WIN32" in result

    def test_cmake_add_library_static(self):
        """Test Cm.add_library for static library."""
        result = Cm.add_library("mylib", "lib.cpp", lib_type="STATIC")
        assert "add_library(mylib STATIC lib.cpp)" in result

    def test_cmake_add_library_shared(self):
        """Test Cm.add_library for shared library."""
        result = Cm.add_library("mylib", "lib.cpp", lib_type="SHARED")
        assert "SHARED" in result

    def test_cmake_target_link_libraries(self):
        """Test Cm.target_link_libraries."""
        result = Cm.target_link_libraries("myapp", "pthread", "ssl")
        assert "target_link_libraries(myapp PUBLIC pthread ssl)" in result

    def test_cmake_target_link_libraries_private(self):
        """Test Cm.target_link_libraries with PRIVATE."""
        result = Cm.target_link_libraries("myapp", "pthread", visibility="PRIVATE")
        assert "PRIVATE" in result

    def test_cmake_target_include_directories(self):
        """Test Cm.target_include_directories."""
        result = Cm.target_include_directories("myapp", "/usr/include", "src")
        assert "target_include_directories(" in result
        assert "/usr/include" in result
        assert "src" in result

    def test_cmake_find_package_simple(self):
        """Test simple Cm.find_package."""
        result = Cm.find_package("OpenSSL")
        assert "find_package(OpenSSL" in result
        assert "REQUIRED" in result

    def test_cmake_find_package_with_version(self):
        """Test Cm.find_package with version."""
        result = Cm.find_package("Boost", version="1.70")
        assert "1.70" in result

    def test_cmake_find_package_with_components(self):
        """Test Cm.find_package with components."""
        result = Cm.find_package("Qt5", components=["Core", "Widgets"])
        assert "COMPONENTS Core Widgets" in result

    def test_cmake_if(self):
        """Test Cm.if_."""
        result = Cm.if_("WIN32", "set(OS Windows)")
        assert "if(WIN32)" in result
        assert "set(OS Windows)" in result
        assert "endif()" in result

    def test_cmake_if_else(self):
        """Test Cm.if_ with else."""
        result = Cm.if_("WIN32", "set(OS Windows)", "set(OS Unix)")
        assert "else()" in result
        assert "set(OS Unix)" in result

    def test_cmake_foreach(self):
        """Test Cm.foreach."""
        result = Cm.foreach("item", "${MY_LIST}", "message(${item})")
        assert "foreach(item ${MY_LIST})" in result
        assert "endforeach()" in result

    def test_cmake_message(self):
        """Test Cm.message."""
        result = Cm.message("Hello World")
        assert 'message(STATUS "Hello World")' in result

    def test_cmake_message_warning(self):
        """Test Cm.message with WARNING."""
        result = Cm.message("Warning!", mode="WARNING")
        assert "WARNING" in result


class TestCMakeGeneratorExpressions:
    """Test CMake generator expression helpers."""

    def test_genex_target_file(self):
        """Test Cm.genex_target_file."""
        result = Cm.genex_target_file("mylib")
        assert result == "$<TARGET_FILE:mylib>"

    def test_genex_config(self):
        """Test Cm.genex_config."""
        result = Cm.genex_config("Debug", "-DDEBUG")
        assert "$<CONFIG:Debug>" in result
        assert "-DDEBUG" in result


class TestCMakeListsGenerator:
    """Test CMakeListsGenerator class."""

    @pytest.fixture
    def temp_cmake(self):
        """Create a temporary CMakeLists.txt for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            temp_path = f.name
        yield temp_path
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass

    def test_generator_creation(self, temp_cmake):
        """Test CMakeListsGenerator creation."""
        gen = CMakeListsGenerator(temp_cmake)
        assert gen.path == temp_cmake
        assert gen.cmake_version == "3.16"

    def test_set_project(self, temp_cmake):
        """Test setting project information."""
        gen = CMakeListsGenerator(temp_cmake)
        gen.set_project("MyProject", version="1.0.0", description="Test project")
        assert gen.project_name == "MyProject"
        assert gen.project_version == "1.0.0"

    def test_set_cxx_standard(self, temp_cmake):
        """Test setting C++ standard."""
        gen = CMakeListsGenerator(temp_cmake)
        gen.set_cxx_standard(17)
        assert gen.cxx_standard == 17

    def test_add_variable(self, temp_cmake):
        """Test adding variables."""
        gen = CMakeListsGenerator(temp_cmake)
        gen.add_variable("MY_VAR", "my_value")
        assert "MY_VAR" in gen.vars

    def test_add_option(self, temp_cmake):
        """Test adding options."""
        gen = CMakeListsGenerator(temp_cmake)
        gen.add_option("ENABLE_TESTS", "Enable testing", True)
        assert "ENABLE_TESTS" in gen.vars

    def test_add_executable(self, temp_cmake):
        """Test adding executable."""
        gen = CMakeListsGenerator(temp_cmake)
        gen.add_executable("myapp", ["main.cpp", "util.cpp"])
        assert "myapp" in gen.executables

    def test_add_library(self, temp_cmake):
        """Test adding library."""
        gen = CMakeListsGenerator(temp_cmake)
        gen.add_library("mylib", ["lib.cpp"], lib_type="SHARED")
        assert "mylib" in gen.libraries
        assert gen.libraries["mylib"]["lib_type"] == "SHARED"

    def test_add_find_package(self, temp_cmake):
        """Test adding find_package."""
        gen = CMakeListsGenerator(temp_cmake)
        gen.add_find_package("OpenSSL", required=True)
        assert len(gen.find_packages) == 1

    def test_generate_basic(self, temp_cmake):
        """Test basic generation."""
        gen = CMakeListsGenerator(temp_cmake)
        gen.set_project("TestProject", version="1.0.0")
        gen.set_cxx_standard(17)
        gen.add_executable("myapp", ["main.cpp"])
        gen.generate()

        with open(temp_cmake, "r") as f:
            content = f.read()

        assert "cmake_minimum_required" in content
        assert "project(TestProject" in content
        assert "CMAKE_CXX_STANDARD 17" in content
        assert "add_executable(myapp main.cpp)" in content

    def test_generate_with_dependencies(self, temp_cmake):
        """Test generation with dependencies."""
        gen = CMakeListsGenerator(temp_cmake)
        gen.set_project("TestProject")
        gen.add_find_package("Threads", required=True)
        gen.add_executable("myapp", ["main.cpp"], link_libraries=["Threads::Threads"])
        gen.generate()

        with open(temp_cmake, "r") as f:
            content = f.read()

        assert "find_package(Threads" in content
        assert "target_link_libraries" in content

    def test_generate_with_library(self, temp_cmake):
        """Test generation with library."""
        gen = CMakeListsGenerator(temp_cmake)
        gen.set_project("TestProject")
        gen.add_library("mylib", ["lib.cpp"], lib_type="STATIC")
        gen.add_executable("myapp", ["main.cpp"], link_libraries=["mylib"])
        gen.generate()

        with open(temp_cmake, "r") as f:
            content = f.read()

        assert "add_library(mylib STATIC lib.cpp)" in content
        assert "add_executable(myapp main.cpp)" in content


class TestCMakeBuilder:
    """Test CMakeBuilder class."""

    def test_builder_creation(self):
        """Test CMakeBuilder creation."""
        builder = CMakeBuilder(source_dir=".", build_dir="build")
        assert builder.source_dir == Path(".")
        assert builder.build_dir == Path("build")

    def test_set_generator(self):
        """Test setting generator."""
        builder = CMakeBuilder()
        builder.set_generator("Ninja")
        assert builder.generator == "Ninja"

    def test_set_option(self):
        """Test setting CMake option."""
        builder = CMakeBuilder()
        builder.set_option("CMAKE_BUILD_TYPE", "Release")
        assert builder.cmake_options["CMAKE_BUILD_TYPE"] == "Release"

    def test_set_option_bool(self):
        """Test setting boolean option."""
        builder = CMakeBuilder()
        builder.set_option("BUILD_TESTS", True)
        assert builder.cmake_options["BUILD_TESTS"] is True

    def test_set_build_type(self):
        """Test set_build_type."""
        builder = CMakeBuilder()
        builder.set_build_type("Debug")
        assert builder.cmake_options["CMAKE_BUILD_TYPE"] == "Debug"
        assert builder.build_config == "Debug"

    def test_set_install_prefix(self):
        """Test set_install_prefix."""
        builder = CMakeBuilder()
        builder.set_install_prefix("/usr/local")
        assert builder.cmake_options["CMAKE_INSTALL_PREFIX"] == "/usr/local"

    def test_add_cxxflags(self):
        """Test adding C++ flags."""
        builder = CMakeBuilder()
        builder.add_cxxflags("-Wall", "-Wextra")
        assert "-Wall" in builder.cmake_options["CMAKE_CXX_FLAGS"]
        assert "-Wextra" in builder.cmake_options["CMAKE_CXX_FLAGS"]

    def test_get_configure_cmd(self):
        """Test get_configure_cmd."""
        builder = CMakeBuilder(source_dir="src", build_dir="build")
        builder.set_generator("Ninja")
        builder.set_option("CMAKE_BUILD_TYPE", "Release")

        cmd = builder.get_configure_cmd()
        assert "cmake" in cmd
        assert "-S" in cmd
        assert "src" in cmd
        assert "-B" in cmd
        assert "build" in cmd
        assert "-G" in cmd
        assert "Ninja" in cmd
        assert "-DCMAKE_BUILD_TYPE=Release" in cmd

    def test_get_build_cmd(self):
        """Test get_build_cmd."""
        builder = CMakeBuilder(build_dir="build")
        builder.set_parallel_jobs(4)
        builder.add_build_target("myapp")

        cmd = builder.get_build_cmd()
        assert "cmake" in cmd
        assert "--build" in cmd
        assert "build" in cmd
        assert "--parallel" in cmd
        assert "4" in cmd
        assert "--target" in cmd
        assert "myapp" in cmd

    def test_dry_run_configure(self, capsys):
        """Test dry run for configure."""
        builder = CMakeBuilder()
        builder.configure(dry_run=True)
        captured = capsys.readouterr()
        assert "cmake" in captured.out

    def test_dry_run_build(self, capsys):
        """Test dry run for build."""
        builder = CMakeBuilder()
        builder.build(dry_run=True)
        captured = capsys.readouterr()
        assert "cmake --build" in captured.out


class TestCMakeIntegration:
    """Integration tests for CMake components."""

    @pytest.fixture
    def temp_cmake(self):
        """Create a temporary CMakeLists.txt for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            temp_path = f.name
        yield temp_path
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass

    def test_full_project_generation(self, temp_cmake):
        """Test generating a complete project."""
        gen = CMakeListsGenerator(temp_cmake)

        # Project setup
        gen.set_project(
            "MyProject",
            version="1.0.0",
            description="A test project",
            languages=["CXX"],
        )
        gen.set_cmake_version("3.16")
        gen.set_cxx_standard(17)

        # Variables
        gen.add_variable("PROJECT_SRC_DIR", "${CMAKE_CURRENT_SOURCE_DIR}/src")
        gen.add_option("BUILD_TESTS", "Enable testing", False)

        # Dependencies
        gen.add_find_package("Threads", required=True)

        # Library
        gen.add_library(
            "mylib",
            ["src/lib.cpp"],
            lib_type="STATIC",
            include_dirs=["include"],
        )

        # Executable
        gen.add_executable(
            "myapp",
            ["src/main.cpp"],
            link_libraries=["mylib", "Threads::Threads"],
            compile_definitions=["MY_APP"],
        )

        # Install
        gen.add_install_target("myapp", "mylib")

        gen.generate()

        with open(temp_cmake, "r") as f:
            content = f.read()

        # Verify all sections present
        assert "cmake_minimum_required(VERSION 3.16" in content
        assert "project(MyProject" in content
        assert "CMAKE_CXX_STANDARD 17" in content
        assert "find_package(Threads" in content
        assert "add_library(mylib STATIC" in content
        assert "add_executable(myapp" in content
        assert "target_link_libraries" in content
        assert "install(TARGETS" in content
