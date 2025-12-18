"""Comprehensive generation tests with file output.

All generated files are written to ./build/test-output/<test-name>/
"""

import pytest
from pathlib import Path

from buildgen import (
    MakefileGenerator,
    CMakeListsGenerator,
    ProjectConfig,
)
from buildgen.common.project import TargetConfig, DependencyConfig


# Output directory for all generated files
OUTPUT_DIR = Path(__file__).parent.parent / "build" / "test-output"


@pytest.fixture(scope="module", autouse=True)
def setup_output_dir():
    """Create the output directory before tests run."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    yield


def get_test_dir(name: str) -> Path:
    """Get or create a test-specific output directory."""
    test_dir = OUTPUT_DIR / name
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


class TestMakefileGeneration:
    """Test Makefile generation with file output."""

    def test_simple_executable(self):
        """Generate Makefile for a simple executable."""
        test_dir = get_test_dir("makefile-simple-executable")
        output = test_dir / "Makefile"

        gen = MakefileGenerator(output)
        gen.cxx = "g++"
        gen.add_cxxflags("-Wall", "-Wextra", "-std=c++17")
        gen.add_target("myapp", "$(CXX) $(CXXFLAGS) -o $@ $^", deps=["main.o"])
        gen.add_pattern_rule("%.o", "%.cpp", "$(CXX) $(CXXFLAGS) -c $< -o $@")
        gen.add_phony("all", "clean")
        gen.add_target("all", deps=["myapp"])
        gen.add_clean("myapp", "*.o")
        gen.generate()

        assert output.exists()
        content = output.read_text()
        assert "CXX = g++" in content
        assert "-std=c++17" in content
        assert "myapp" in content

    def test_static_library(self):
        """Generate Makefile for a static library."""
        test_dir = get_test_dir("makefile-static-library")
        output = test_dir / "Makefile"

        # Create include dir for validation
        (test_dir / "include").mkdir(exist_ok=True)
        (test_dir / "src").mkdir(exist_ok=True)

        gen = MakefileGenerator(output)
        gen.add_variable("AR", "ar")
        gen.add_variable("ARFLAGS", "rcs")
        gen.add_cxxflags("-Wall", "-fPIC")
        gen.add_include_dirs(str(test_dir / "include"))

        gen.add_target("libmylib.a", "$(AR) $(ARFLAGS) $@ $^", deps=["src/lib.o", "src/utils.o"])
        gen.add_pattern_rule("%.o", "%.cpp", "$(CXX) $(CXXFLAGS) -c $< -o $@")
        gen.add_phony("all", "clean")
        gen.add_target("all", deps=["libmylib.a"])
        gen.add_clean("libmylib.a", "src/*.o")
        gen.generate()

        assert output.exists()
        content = output.read_text()
        assert "AR = ar" in content
        assert "libmylib.a" in content
        assert "-fPIC" in content

    def test_shared_library(self):
        """Generate Makefile for a shared library."""
        test_dir = get_test_dir("makefile-shared-library")
        output = test_dir / "Makefile"

        # Create include dir for validation
        (test_dir / "include").mkdir(exist_ok=True)
        (test_dir / "src").mkdir(exist_ok=True)

        gen = MakefileGenerator(output)
        gen.add_cxxflags("-Wall", "-fPIC", "-std=c++17")
        gen.add_include_dirs(str(test_dir / "include"))

        gen.add_target(
            "libmylib.so",
            "$(CXX) -shared -o $@ $^ $(LDFLAGS)",
            deps=["src/lib.o", "src/utils.o"]
        )
        gen.add_pattern_rule("%.o", "%.cpp", "$(CXX) $(CXXFLAGS) -c $< -o $@")
        gen.add_phony("all", "clean")
        gen.add_target("all", deps=["libmylib.so"])
        gen.add_clean("libmylib.so", "src/*.o")
        gen.generate()

        assert output.exists()
        content = output.read_text()
        assert "libmylib.so" in content
        assert "-shared" in content

    def test_multi_target(self):
        """Generate Makefile with multiple targets."""
        test_dir = get_test_dir("makefile-multi-target")
        output = test_dir / "Makefile"

        # Create directories for validation
        (test_dir / "include").mkdir(exist_ok=True)
        (test_dir / "src").mkdir(exist_ok=True)
        (test_dir / "tests").mkdir(exist_ok=True)

        gen = MakefileGenerator(output)
        gen.add_cxxflags("-Wall", "-std=c++17")
        gen.add_include_dirs(str(test_dir / "include"))

        # Library
        gen.add_target("libcore.a", "$(AR) rcs $@ $^", deps=["src/core.o"])

        # Main executable
        gen.add_target(
            "myapp",
            "$(CXX) $(CXXFLAGS) -o $@ $^ -L. -lcore",
            deps=["src/main.o", "libcore.a"]
        )

        # Test executable
        gen.add_target(
            "test_runner",
            "$(CXX) $(CXXFLAGS) -o $@ $^ -L. -lcore",
            deps=["tests/test_main.o", "libcore.a"]
        )

        gen.add_pattern_rule("%.o", "%.cpp", "$(CXX) $(CXXFLAGS) -c $< -o $@")
        gen.add_phony("all", "clean", "test")
        gen.add_target("all", deps=["myapp"])
        gen.add_target("test", deps=["test_runner"])
        gen.add_clean("myapp", "test_runner", "libcore.a", "src/*.o", "tests/*.o")
        gen.generate()

        assert output.exists()
        content = output.read_text()
        assert "libcore.a" in content
        assert "myapp" in content
        assert "test_runner" in content

    def test_with_conditionals(self):
        """Generate Makefile with conditional blocks."""
        test_dir = get_test_dir("makefile-conditionals")
        output = test_dir / "Makefile"

        gen = MakefileGenerator(output)
        gen.add_variable("DEBUG", "1")
        gen.add_conditional(
            "ifeq",
            "$(DEBUG),1",
            "CXXFLAGS += -g -O0 -DDEBUG",
            "CXXFLAGS += -O2 -DNDEBUG"
        )
        gen.add_target("myapp", "$(CXX) $(CXXFLAGS) -o $@ $^", deps=["main.o"])
        gen.add_phony("all")
        gen.add_target("all", deps=["myapp"])
        gen.generate()

        assert output.exists()
        content = output.read_text()
        assert "ifeq ($(DEBUG),1)" in content
        assert "-g -O0 -DDEBUG" in content
        assert "-O2 -DNDEBUG" in content

    def test_with_includes(self):
        """Generate Makefile with include directives."""
        test_dir = get_test_dir("makefile-includes")
        output = test_dir / "Makefile"

        # Create a config.mk file to include
        config_mk = test_dir / "config.mk"
        config_mk.write_text("# Configuration\nPREFIX ?= /usr/local\n")

        gen = MakefileGenerator(output)
        gen.add_include("config.mk")
        gen.add_include_optional("local.mk")
        gen.add_target("install", "@echo Installing to $(PREFIX)")
        gen.add_phony("install")
        gen.generate()

        assert output.exists()
        content = output.read_text()
        assert "include config.mk" in content
        assert "-include local.mk" in content


class TestCMakeGeneration:
    """Test CMake generation with file output."""

    def test_simple_executable(self):
        """Generate CMakeLists.txt for a simple executable."""
        test_dir = get_test_dir("cmake-simple-executable")
        output = test_dir / "CMakeLists.txt"

        gen = CMakeListsGenerator(output)
        gen.set_cmake_version("3.16")
        gen.set_project("myapp", version="1.0.0", languages=["CXX"])
        gen.set_cxx_standard(17)
        gen.add_executable("myapp", ["src/main.cpp"])
        gen.generate()

        assert output.exists()
        content = output.read_text()
        assert "cmake_minimum_required(VERSION 3.16" in content
        assert "project(myapp" in content
        assert "CMAKE_CXX_STANDARD 17" in content
        assert "add_executable(myapp" in content

    def test_static_library(self):
        """Generate CMakeLists.txt for a static library."""
        test_dir = get_test_dir("cmake-static-library")
        output = test_dir / "CMakeLists.txt"

        gen = CMakeListsGenerator(output)
        gen.set_cmake_version("3.16")
        gen.set_project("mylib", version="1.0.0", languages=["CXX"])
        gen.set_cxx_standard(17)
        gen.add_library(
            "mylib",
            ["src/lib.cpp", "src/utils.cpp"],
            lib_type="STATIC",
            include_dirs=["include"],
        )
        gen.add_install_target("mylib")
        gen.generate()

        assert output.exists()
        content = output.read_text()
        assert "add_library(mylib STATIC" in content
        assert "install(TARGETS mylib" in content

    def test_shared_library(self):
        """Generate CMakeLists.txt for a shared library."""
        test_dir = get_test_dir("cmake-shared-library")
        output = test_dir / "CMakeLists.txt"

        gen = CMakeListsGenerator(output)
        gen.set_cmake_version("3.16")
        gen.set_project("mylib", version="2.0.0", languages=["CXX"])
        gen.set_cxx_standard(17)
        gen.add_library(
            "mylib",
            ["src/lib.cpp"],
            lib_type="SHARED",
            include_dirs=["include"],
            compile_definitions=["MYLIB_EXPORTS"],
        )
        gen.generate()

        assert output.exists()
        content = output.read_text()
        assert "add_library(mylib SHARED" in content
        assert "MYLIB_EXPORTS" in content

    def test_with_find_package(self):
        """Generate CMakeLists.txt with find_package dependencies."""
        test_dir = get_test_dir("cmake-find-package")
        output = test_dir / "CMakeLists.txt"

        gen = CMakeListsGenerator(output)
        gen.set_cmake_version("3.16")
        gen.set_project("myapp", version="1.0.0", languages=["CXX"])
        gen.set_cxx_standard(17)
        gen.add_find_package("Threads", required=True)
        gen.add_find_package("OpenSSL", version="1.1", required=True)
        gen.add_find_package("Boost", version="1.70", components=["filesystem", "system"])
        gen.add_executable(
            "myapp",
            ["src/main.cpp"],
            link_libraries=["Threads::Threads", "OpenSSL::SSL", "Boost::filesystem"],
        )
        gen.generate()

        assert output.exists()
        content = output.read_text()
        assert "find_package(Threads REQUIRED)" in content
        assert "find_package(OpenSSL 1.1 REQUIRED)" in content
        assert "find_package(Boost 1.70 COMPONENTS filesystem system" in content
        assert "target_link_libraries(myapp" in content

    def test_with_fetchcontent(self):
        """Generate CMakeLists.txt with FetchContent dependencies."""
        test_dir = get_test_dir("cmake-fetchcontent")
        output = test_dir / "CMakeLists.txt"

        gen = CMakeListsGenerator(output)
        gen.set_cmake_version("3.16")
        gen.set_project("myapp", version="1.0.0", languages=["CXX"])
        gen.set_cxx_standard(17)
        gen.add_fetchcontent(
            "fmt",
            git_repository="https://github.com/fmtlib/fmt.git",
            git_tag="10.1.1",
        )
        gen.add_fetchcontent(
            "nlohmann_json",
            git_repository="https://github.com/nlohmann/json.git",
            git_tag="v3.11.2",
        )
        gen.add_executable(
            "myapp",
            ["src/main.cpp"],
            link_libraries=["fmt::fmt", "nlohmann_json::nlohmann_json"],
        )
        gen.generate()

        assert output.exists()
        content = output.read_text()
        assert "FetchContent_Declare" in content
        assert "fmt" in content
        assert "nlohmann_json" in content
        assert "FetchContent_MakeAvailable" in content

    def test_multi_target(self):
        """Generate CMakeLists.txt with multiple targets."""
        test_dir = get_test_dir("cmake-multi-target")
        output = test_dir / "CMakeLists.txt"

        gen = CMakeListsGenerator(output)
        gen.set_cmake_version("3.16")
        gen.set_project("myproject", version="1.0.0", languages=["CXX"])
        gen.set_cxx_standard(17)

        # Core library
        gen.add_library(
            "core",
            ["src/core.cpp"],
            lib_type="STATIC",
            include_dirs=["include"],
        )

        # Main executable
        gen.add_executable(
            "myapp",
            ["src/main.cpp"],
            link_libraries=["core"],
        )

        # Test executable
        gen.add_executable(
            "myapp_tests",
            ["tests/test_main.cpp"],
            link_libraries=["core"],
        )

        gen.add_install_target("myapp", "core")
        gen.generate()

        assert output.exists()
        content = output.read_text()
        assert "add_library(core STATIC" in content
        assert "add_executable(myapp" in content
        assert "add_executable(myapp_tests" in content

    def test_with_compile_options(self):
        """Generate CMakeLists.txt with compile options and definitions."""
        test_dir = get_test_dir("cmake-compile-options")
        output = test_dir / "CMakeLists.txt"

        gen = CMakeListsGenerator(output)
        gen.set_cmake_version("3.16")
        gen.set_project("myapp", version="1.0.0", languages=["CXX"])
        gen.set_cxx_standard(20)
        gen.add_cxxflags("-Wall", "-Wextra", "-Wpedantic")
        gen.add_executable(
            "myapp",
            ["src/main.cpp"],
            compile_definitions=["DEBUG", "VERSION=\\\"1.0.0\\\""],
            compile_options=["-fno-rtti"],
        )
        gen.generate()

        assert output.exists()
        content = output.read_text()
        assert "CMAKE_CXX_STANDARD 20" in content
        assert "-Wall" in content
        assert "DEBUG" in content


class TestProjectConfigGeneration:
    """Test ProjectConfig cross-generator generation with file output."""

    def test_simple_executable(self):
        """Generate both Makefile and CMakeLists.txt for simple executable."""
        test_dir = get_test_dir("project-simple-executable")

        config = ProjectConfig(
            name="myapp",
            version="1.0.0",
            cxx_standard=17,
            compile_options=["-Wall", "-Wextra"],
            targets=[
                TargetConfig(
                    name="myapp",
                    target_type="executable",
                    sources=["src/main.cpp"],
                ),
            ],
        )

        config.generate_all(
            makefile_path=test_dir / "Makefile",
            cmake_path=test_dir / "CMakeLists.txt",
        )

        assert (test_dir / "Makefile").exists()
        assert (test_dir / "CMakeLists.txt").exists()

        makefile = (test_dir / "Makefile").read_text()
        cmake = (test_dir / "CMakeLists.txt").read_text()

        assert "myapp" in makefile
        assert "myapp" in cmake
        assert "-std=c++17" in makefile
        assert "CMAKE_CXX_STANDARD 17" in cmake

    def test_static_library(self):
        """Generate both files for static library."""
        test_dir = get_test_dir("project-static-library")

        config = ProjectConfig(
            name="mylib",
            version="1.0.0",
            cxx_standard=17,
            targets=[
                TargetConfig(
                    name="mylib",
                    target_type="static",
                    sources=["src/lib.cpp", "src/utils.cpp"],
                    include_dirs=["include"],
                    install=True,
                ),
            ],
        )

        config.generate_all(
            makefile_path=test_dir / "Makefile",
            cmake_path=test_dir / "CMakeLists.txt",
        )

        makefile = (test_dir / "Makefile").read_text()
        cmake = (test_dir / "CMakeLists.txt").read_text()

        assert "libmylib.a" in makefile
        assert "add_library(mylib STATIC" in cmake
        assert "install(TARGETS mylib" in cmake

    def test_shared_library(self):
        """Generate both files for shared library."""
        test_dir = get_test_dir("project-shared-library")

        config = ProjectConfig(
            name="mylib",
            version="2.0.0",
            cxx_standard=17,
            targets=[
                TargetConfig(
                    name="mylib",
                    target_type="shared",
                    sources=["src/lib.cpp"],
                    include_dirs=["include"],
                ),
            ],
        )

        config.generate_all(
            makefile_path=test_dir / "Makefile",
            cmake_path=test_dir / "CMakeLists.txt",
        )

        makefile = (test_dir / "Makefile").read_text()
        cmake = (test_dir / "CMakeLists.txt").read_text()

        assert "libmylib.so" in makefile
        assert "-shared" in makefile
        assert "add_library(mylib SHARED" in cmake

    def test_with_dependencies(self):
        """Generate both files with external dependencies."""
        test_dir = get_test_dir("project-with-dependencies")

        config = ProjectConfig(
            name="myapp",
            version="1.0.0",
            cxx_standard=17,
            dependencies=[
                DependencyConfig(name="Threads"),
                DependencyConfig(name="OpenSSL", required=True),
            ],
            targets=[
                TargetConfig(
                    name="myapp",
                    target_type="executable",
                    sources=["src/main.cpp"],
                    link_libraries=["Threads::Threads", "OpenSSL::SSL"],
                ),
            ],
        )

        config.generate_all(
            makefile_path=test_dir / "Makefile",
            cmake_path=test_dir / "CMakeLists.txt",
        )

        makefile = (test_dir / "Makefile").read_text()
        cmake = (test_dir / "CMakeLists.txt").read_text()

        assert "-lpthread" in makefile
        assert "find_package(Threads REQUIRED)" in cmake
        assert "find_package(OpenSSL REQUIRED)" in cmake

    def test_with_fetchcontent(self):
        """Generate both files with FetchContent dependencies."""
        test_dir = get_test_dir("project-with-fetchcontent")

        config = ProjectConfig(
            name="myapp",
            version="1.0.0",
            cxx_standard=17,
            dependencies=[
                DependencyConfig(
                    name="fmt",
                    git_repository="https://github.com/fmtlib/fmt.git",
                    git_tag="10.1.1",
                ),
            ],
            targets=[
                TargetConfig(
                    name="myapp",
                    target_type="executable",
                    sources=["src/main.cpp"],
                    link_libraries=["fmt::fmt"],
                ),
            ],
        )

        config.generate_all(
            makefile_path=test_dir / "Makefile",
            cmake_path=test_dir / "CMakeLists.txt",
        )

        cmake = (test_dir / "CMakeLists.txt").read_text()

        assert "FetchContent_Declare" in cmake
        assert "fmt" in cmake
        assert "https://github.com/fmtlib/fmt.git" in cmake

    def test_multi_target_project(self):
        """Generate both files for multi-target project."""
        test_dir = get_test_dir("project-multi-target")

        config = ProjectConfig(
            name="myproject",
            version="1.0.0",
            cxx_standard=17,
            compile_options=["-Wall"],
            targets=[
                TargetConfig(
                    name="core",
                    target_type="static",
                    sources=["src/core.cpp"],
                    include_dirs=["include"],
                ),
                TargetConfig(
                    name="myapp",
                    target_type="executable",
                    sources=["src/main.cpp"],
                    link_libraries=["core"],
                    install=True,
                ),
                TargetConfig(
                    name="myapp_tests",
                    target_type="executable",
                    sources=["tests/test_main.cpp"],
                    link_libraries=["core"],
                ),
            ],
        )

        config.generate_all(
            makefile_path=test_dir / "Makefile",
            cmake_path=test_dir / "CMakeLists.txt",
        )

        makefile = (test_dir / "Makefile").read_text()
        cmake = (test_dir / "CMakeLists.txt").read_text()

        # Check Makefile
        assert "libcore.a" in makefile
        assert "myapp" in makefile
        assert "myapp_tests" in makefile

        # Check CMake
        assert "add_library(core STATIC" in cmake
        assert "add_executable(myapp" in cmake
        assert "add_executable(myapp_tests" in cmake
        assert "install(TARGETS myapp" in cmake

    def test_full_project_from_json(self):
        """Generate from JSON config file."""
        test_dir = get_test_dir("project-from-json")

        # Write JSON config
        json_config = test_dir / "project.json"
        json_config.write_text("""{
    "name": "fullproject",
    "version": "1.0.0",
    "description": "A full featured project",
    "cxx_standard": 17,
    "compile_options": ["-Wall", "-Wextra"],
    "dependencies": [
        "Threads",
        {"name": "OpenSSL", "required": true}
    ],
    "targets": [
        {
            "name": "mylib",
            "type": "static",
            "sources": ["src/lib.cpp"],
            "include_dirs": ["include"],
            "install": true
        },
        {
            "name": "myapp",
            "type": "executable",
            "sources": ["src/main.cpp"],
            "link_libraries": ["mylib", "Threads::Threads", "OpenSSL::SSL"],
            "install": true
        }
    ]
}""")

        # Load and generate
        config = ProjectConfig.load(json_config)
        config.generate_all(
            makefile_path=test_dir / "Makefile",
            cmake_path=test_dir / "CMakeLists.txt",
        )

        assert (test_dir / "Makefile").exists()
        assert (test_dir / "CMakeLists.txt").exists()

        cmake = (test_dir / "CMakeLists.txt").read_text()
        assert "project(fullproject" in cmake
        assert "find_package(Threads REQUIRED)" in cmake
        assert "find_package(OpenSSL REQUIRED)" in cmake


class TestBuildTypeTemplates:
    """Test project init templates generate valid output."""

    def test_executable_template(self):
        """Test executable template generation."""
        test_dir = get_test_dir("template-executable")

        config = ProjectConfig(
            name="myapp",
            version="1.0.0",
            description="A executable project",
            cxx_standard=17,
            compile_options=["-Wall", "-Wextra"],
            targets=[
                TargetConfig(
                    name="myapp",
                    target_type="executable",
                    sources=["src/main.cpp"],
                    install=True,
                ),
            ],
        )

        config.generate_all(
            makefile_path=test_dir / "Makefile",
            cmake_path=test_dir / "CMakeLists.txt",
        )

        # Also save the config
        config.to_json(test_dir / "project.json")

        assert (test_dir / "Makefile").exists()
        assert (test_dir / "CMakeLists.txt").exists()
        assert (test_dir / "project.json").exists()

    def test_library_with_tests_template(self):
        """Test library-with-tests template generation."""
        test_dir = get_test_dir("template-library-with-tests")

        config = ProjectConfig(
            name="mylib",
            version="1.0.0",
            description="A library-with-tests project",
            cxx_standard=17,
            compile_options=["-Wall", "-Wextra"],
            targets=[
                TargetConfig(
                    name="mylib",
                    target_type="static",
                    sources=["src/lib.cpp"],
                    include_dirs=["include"],
                    install=True,
                ),
                TargetConfig(
                    name="mylib_tests",
                    target_type="executable",
                    sources=["tests/test_main.cpp"],
                    include_dirs=["include"],
                    link_libraries=["mylib"],
                ),
            ],
        )

        config.generate_all(
            makefile_path=test_dir / "Makefile",
            cmake_path=test_dir / "CMakeLists.txt",
        )
        config.to_json(test_dir / "project.json")

        cmake = (test_dir / "CMakeLists.txt").read_text()
        assert "add_library(mylib STATIC" in cmake
        assert "add_executable(mylib_tests" in cmake

    def test_full_template(self):
        """Test full template generation."""
        test_dir = get_test_dir("template-full")

        config = ProjectConfig(
            name="myproj",
            version="1.0.0",
            description="A full project",
            cxx_standard=17,
            compile_options=["-Wall", "-Wextra"],
            dependencies=[
                DependencyConfig(name="Threads"),
            ],
            targets=[
                TargetConfig(
                    name="myproj_lib",
                    target_type="static",
                    sources=["src/lib.cpp"],
                    include_dirs=["include"],
                    install=True,
                ),
                TargetConfig(
                    name="myproj",
                    target_type="executable",
                    sources=["src/main.cpp"],
                    link_libraries=["myproj_lib", "Threads::Threads"],
                    install=True,
                ),
                TargetConfig(
                    name="myproj_tests",
                    target_type="executable",
                    sources=["tests/test_main.cpp"],
                    include_dirs=["include"],
                    link_libraries=["myproj_lib"],
                ),
            ],
        )

        config.generate_all(
            makefile_path=test_dir / "Makefile",
            cmake_path=test_dir / "CMakeLists.txt",
        )
        config.to_json(test_dir / "project.json")

        makefile = (test_dir / "Makefile").read_text()
        cmake = (test_dir / "CMakeLists.txt").read_text()

        # Verify all targets present
        assert "libmyproj_lib.a" in makefile
        assert "myproj" in makefile
        assert "myproj_tests" in makefile

        assert "add_library(myproj_lib STATIC" in cmake
        assert "add_executable(myproj " in cmake
        assert "add_executable(myproj_tests" in cmake
        assert "find_package(Threads REQUIRED)" in cmake
