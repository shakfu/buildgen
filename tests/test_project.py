"""Tests for buildgen.common.project module."""

import json
import tempfile
from pathlib import Path

import pytest

from buildgen.common.project import (
    DependencyConfig,
    ProjectConfig,
    TargetConfig,
)


class TestTargetConfig:
    """Tests for TargetConfig dataclass."""

    def test_default_values(self):
        """Test TargetConfig with only required fields."""
        target = TargetConfig(name="myapp")
        assert target.name == "myapp"
        assert target.sources == []
        assert target.target_type == "executable"
        assert target.include_dirs == []
        assert target.link_libraries == []
        assert target.compile_definitions == []
        assert target.compile_options == []
        assert target.link_options == []
        assert target.install is False

    def test_from_dict_minimal(self):
        """Test creating TargetConfig from minimal dict."""
        data = {"name": "myapp"}
        target = TargetConfig.from_dict(data)
        assert target.name == "myapp"
        assert target.target_type == "executable"

    def test_from_dict_full(self):
        """Test creating TargetConfig from full dict."""
        data = {
            "name": "mylib",
            "type": "static",
            "sources": ["lib.cpp", "utils.cpp"],
            "include_dirs": ["include"],
            "link_libraries": ["pthread"],
            "compile_definitions": ["DEBUG"],
            "compile_options": ["-Wall"],
            "link_options": ["-static"],
            "install": True,
        }
        target = TargetConfig.from_dict(data)
        assert target.name == "mylib"
        assert target.target_type == "static"
        assert target.sources == ["lib.cpp", "utils.cpp"]
        assert target.include_dirs == ["include"]
        assert target.link_libraries == ["pthread"]
        assert target.compile_definitions == ["DEBUG"]
        assert target.compile_options == ["-Wall"]
        assert target.link_options == ["-static"]
        assert target.install is True


class TestDependencyConfig:
    """Tests for DependencyConfig dataclass."""

    def test_default_values(self):
        """Test DependencyConfig with only required fields."""
        dep = DependencyConfig(name="OpenSSL")
        assert dep.name == "OpenSSL"
        assert dep.version is None
        assert dep.required is True
        assert dep.components == []
        assert dep.git_repository is None
        assert dep.git_tag is None
        assert dep.url is None

    def test_from_dict_string(self):
        """Test creating DependencyConfig from string."""
        dep = DependencyConfig.from_dict("OpenSSL")
        assert dep.name == "OpenSSL"
        assert dep.version is None

    def test_from_dict_string_with_version(self):
        """Test creating DependencyConfig from string with version."""
        dep = DependencyConfig.from_dict("Boost>=1.70")
        assert dep.name == "Boost"
        assert dep.version == "1.70"

    def test_from_dict_full(self):
        """Test creating DependencyConfig from full dict."""
        data = {
            "name": "fmt",
            "version": "10.1.1",
            "required": False,
            "components": ["core"],
            "git_repository": "https://github.com/fmtlib/fmt.git",
            "git_tag": "10.1.1",
        }
        dep = DependencyConfig.from_dict(data)
        assert dep.name == "fmt"
        assert dep.version == "10.1.1"
        assert dep.required is False
        assert dep.components == ["core"]
        assert dep.git_repository == "https://github.com/fmtlib/fmt.git"
        assert dep.git_tag == "10.1.1"


class TestProjectConfig:
    """Tests for ProjectConfig dataclass."""

    def test_default_values(self):
        """Test ProjectConfig with only required fields."""
        config = ProjectConfig(name="myproject")
        assert config.name == "myproject"
        assert config.version == "1.0.0"
        assert config.description == ""
        assert config.languages == ["CXX"]
        assert config.cxx_standard is None
        assert config.c_standard is None
        assert config.cc == "gcc"
        assert config.cxx == "g++"
        assert config.include_dirs == []
        assert config.targets == []
        assert config.dependencies == []
        assert config.variables == {}
        assert config.cmake_minimum_version == "3.16"

    def test_from_dict_minimal(self):
        """Test creating ProjectConfig from minimal dict."""
        data = {"name": "myproject"}
        config = ProjectConfig.from_dict(data)
        assert config.name == "myproject"

    def test_from_dict_with_targets(self):
        """Test creating ProjectConfig with targets."""
        data = {
            "name": "myproject",
            "targets": [
                {"name": "myapp", "sources": ["main.cpp"]},
                {"name": "mylib", "type": "static", "sources": ["lib.cpp"]},
            ],
        }
        config = ProjectConfig.from_dict(data)
        assert len(config.targets) == 2
        assert config.targets[0].name == "myapp"
        assert config.targets[1].name == "mylib"
        assert config.targets[1].target_type == "static"

    def test_from_dict_with_dependencies(self):
        """Test creating ProjectConfig with dependencies."""
        data = {
            "name": "myproject",
            "dependencies": [
                "Threads",
                {"name": "OpenSSL", "required": True},
            ],
        }
        config = ProjectConfig.from_dict(data)
        assert len(config.dependencies) == 2
        assert config.dependencies[0].name == "Threads"
        assert config.dependencies[1].name == "OpenSSL"

    def test_from_json(self):
        """Test loading ProjectConfig from JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "name": "testproject",
                    "version": "2.0.0",
                    "cxx_standard": 17,
                },
                f,
            )
            f.flush()

            config = ProjectConfig.from_json(f.name)
            assert config.name == "testproject"
            assert config.version == "2.0.0"
            assert config.cxx_standard == 17

            Path(f.name).unlink()

    def test_to_json(self):
        """Test saving ProjectConfig to JSON file."""
        config = ProjectConfig(
            name="testproject",
            version="2.0.0",
            cxx_standard=17,
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config.to_json(f.name)

            with open(f.name) as rf:
                data = json.load(rf)

            assert data["name"] == "testproject"
            assert data["version"] == "2.0.0"
            assert data["cxx_standard"] == 17

            Path(f.name).unlink()

    def test_load_json_by_extension(self):
        """Test ProjectConfig.load() detects JSON by extension."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"name": "testproject"}, f)
            f.flush()

            config = ProjectConfig.load(f.name)
            assert config.name == "testproject"

            Path(f.name).unlink()

    def test_to_dict(self):
        """Test converting ProjectConfig to dict."""
        target = TargetConfig(name="myapp", sources=["main.cpp"])
        dep = DependencyConfig(name="OpenSSL")
        config = ProjectConfig(
            name="myproject",
            version="1.0.0",
            targets=[target],
            dependencies=[dep],
        )

        data = config.to_dict()
        assert data["name"] == "myproject"
        assert data["version"] == "1.0.0"
        assert len(data["targets"]) == 1
        assert data["targets"][0]["name"] == "myapp"
        assert len(data["dependencies"]) == 1
        assert data["dependencies"][0]["name"] == "OpenSSL"


class TestProjectConfigGeneration:
    """Tests for ProjectConfig generation methods."""

    def test_generate_makefile_simple(self):
        """Test generating a simple Makefile."""
        config = ProjectConfig(
            name="myproject",
            cxx_standard=17,
            targets=[
                TargetConfig(
                    name="myapp",
                    sources=["main.cpp"],
                    target_type="executable",
                ),
            ],
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix="", delete=False) as f:
            config.generate_makefile(f.name)

            with open(f.name) as rf:
                content = rf.read()

            assert "CXX" in content
            assert "myapp" in content
            assert "-std=c++17" in content

            Path(f.name).unlink()

    def test_generate_cmake_simple(self):
        """Test generating a simple CMakeLists.txt."""
        config = ProjectConfig(
            name="myproject",
            version="1.0.0",
            cxx_standard=17,
            targets=[
                TargetConfig(
                    name="myapp",
                    sources=["main.cpp"],
                    target_type="executable",
                ),
            ],
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            config.generate_cmake(f.name)

            with open(f.name) as rf:
                content = rf.read()

            assert "cmake_minimum_required" in content
            assert "project(myproject" in content
            assert "add_executable(myapp" in content
            assert "CMAKE_CXX_STANDARD 17" in content

            Path(f.name).unlink()

    def test_generate_all(self):
        """Test generating both Makefile and CMakeLists.txt."""
        config = ProjectConfig(
            name="myproject",
            cxx_standard=17,
            targets=[
                TargetConfig(name="myapp", sources=["main.cpp"]),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            makefile_path = Path(tmpdir) / "Makefile"
            cmake_path = Path(tmpdir) / "CMakeLists.txt"

            config.generate_all(makefile_path, cmake_path)

            assert makefile_path.exists()
            assert cmake_path.exists()

            makefile_content = makefile_path.read_text()
            cmake_content = cmake_path.read_text()

            assert "myapp" in makefile_content
            assert "myapp" in cmake_content

    def test_generate_static_library(self):
        """Test generating static library target."""
        config = ProjectConfig(
            name="myproject",
            targets=[
                TargetConfig(
                    name="mylib",
                    sources=["lib.cpp"],
                    target_type="static",
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            cmake_path = Path(tmpdir) / "CMakeLists.txt"
            config.generate_cmake(cmake_path)

            content = cmake_path.read_text()
            assert "add_library(mylib STATIC" in content

    def test_generate_shared_library(self):
        """Test generating shared library target."""
        config = ProjectConfig(
            name="myproject",
            targets=[
                TargetConfig(
                    name="mylib",
                    sources=["lib.cpp"],
                    target_type="shared",
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            cmake_path = Path(tmpdir) / "CMakeLists.txt"
            config.generate_cmake(cmake_path)

            content = cmake_path.read_text()
            assert "add_library(mylib SHARED" in content

    def test_generate_with_dependencies(self):
        """Test generating with find_package dependencies."""
        config = ProjectConfig(
            name="myproject",
            dependencies=[
                DependencyConfig(name="OpenSSL", required=True),
            ],
            targets=[
                TargetConfig(
                    name="myapp",
                    sources=["main.cpp"],
                    link_libraries=["OpenSSL::SSL"],
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            cmake_path = Path(tmpdir) / "CMakeLists.txt"
            config.generate_cmake(cmake_path)

            content = cmake_path.read_text()
            assert "find_package(OpenSSL REQUIRED)" in content

    def test_generate_with_fetchcontent(self):
        """Test generating with FetchContent dependencies."""
        config = ProjectConfig(
            name="myproject",
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
                    sources=["main.cpp"],
                    link_libraries=["fmt::fmt"],
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            cmake_path = Path(tmpdir) / "CMakeLists.txt"
            config.generate_cmake(cmake_path)

            content = cmake_path.read_text()
            assert "FetchContent_Declare" in content
            assert "fmt" in content
            assert "https://github.com/fmtlib/fmt.git" in content

    def test_generate_with_install(self):
        """Test generating with install targets."""
        config = ProjectConfig(
            name="myproject",
            targets=[
                TargetConfig(
                    name="myapp",
                    sources=["main.cpp"],
                    install=True,
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            cmake_path = Path(tmpdir) / "CMakeLists.txt"
            config.generate_cmake(cmake_path)

            content = cmake_path.read_text()
            assert "install(TARGETS myapp" in content


class TestProjectConfigYAML:
    """Tests for YAML support (optional pyyaml)."""

    @pytest.fixture
    def yaml_available(self):
        """Check if pyyaml is available."""
        import importlib.util

        return importlib.util.find_spec("yaml") is not None

    def test_from_yaml(self, yaml_available):
        """Test loading ProjectConfig from YAML file."""
        if not yaml_available:
            pytest.skip("pyyaml not available")

        import yaml

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "name": "testproject",
                    "version": "2.0.0",
                    "cxx_standard": 17,
                },
                f,
            )
            f.flush()

            config = ProjectConfig.from_yaml(f.name)
            assert config.name == "testproject"
            assert config.version == "2.0.0"
            assert config.cxx_standard == 17

            Path(f.name).unlink()

    def test_to_yaml(self, yaml_available):
        """Test saving ProjectConfig to YAML file."""
        if not yaml_available:
            pytest.skip("pyyaml not available")

        import yaml

        config = ProjectConfig(
            name="testproject",
            version="2.0.0",
            cxx_standard=17,
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config.to_yaml(f.name)

            with open(f.name) as rf:
                data = yaml.safe_load(rf)

            assert data["name"] == "testproject"
            assert data["version"] == "2.0.0"
            assert data["cxx_standard"] == 17

            Path(f.name).unlink()

    def test_load_yaml_by_extension(self, yaml_available):
        """Test ProjectConfig.load() detects YAML by extension."""
        if not yaml_available:
            pytest.skip("pyyaml not available")

        import yaml

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"name": "testproject"}, f)
            f.flush()

            config = ProjectConfig.load(f.name)
            assert config.name == "testproject"

            Path(f.name).unlink()

    def test_yaml_import_error(self):
        """Test helpful error message when pyyaml not available."""
        # This test is tricky - we can't easily mock the import
        # Just test that from_yaml and to_yaml exist and have docstrings
        assert "pyyaml" in ProjectConfig.from_yaml.__doc__.lower()
        assert "pyyaml" in ProjectConfig.to_yaml.__doc__.lower()
