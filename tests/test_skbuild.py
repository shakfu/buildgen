"""Tests for scikit-build-core project generation."""

import pytest

from buildgen.skbuild.generator import (
    SkbuildProjectGenerator,
    get_skbuild_types,
    is_skbuild_type,
)
from buildgen.skbuild.templates import TEMPLATES, SKBUILD_TYPES


class TestSkbuildTypes:
    """Test skbuild type utilities."""

    def test_get_skbuild_types(self):
        """Test get_skbuild_types returns all types."""
        types = get_skbuild_types()
        assert "skbuild-pybind11" in types
        assert "skbuild-cython" in types
        assert "skbuild-c" in types
        assert "skbuild-nanobind" in types
        assert len(types) == 4

    def test_is_skbuild_type(self):
        """Test is_skbuild_type detection."""
        assert is_skbuild_type("skbuild-pybind11")
        assert is_skbuild_type("skbuild-cython")
        assert is_skbuild_type("skbuild-c")
        assert is_skbuild_type("skbuild-nanobind")
        assert not is_skbuild_type("executable")
        assert not is_skbuild_type("static")
        assert not is_skbuild_type("unknown")


class TestTemplates:
    """Test template definitions."""

    def test_all_types_have_templates(self):
        """Test all SKBUILD_TYPES have corresponding templates."""
        for template_type in SKBUILD_TYPES:
            assert template_type in TEMPLATES

    def test_templates_have_required_files(self):
        """Test all templates include required files."""
        required_files = ["Makefile", "pyproject.toml", "CMakeLists.txt"]
        for template_type, files in TEMPLATES.items():
            for required in required_files:
                assert required in files, f"{template_type} missing {required}"

    def test_templates_have_source_files(self):
        """Test all templates include source files."""
        for template_type, files in TEMPLATES.items():
            source_files = [f for f in files if "/_core." in f]
            assert len(source_files) == 1, (
                f"{template_type} should have one _core source file"
            )

    def test_templates_have_init_py(self):
        """Test all templates include __init__.py."""
        for template_type, files in TEMPLATES.items():
            init_files = [f for f in files if "__init__.py" in f]
            assert len(init_files) == 1, f"{template_type} should have __init__.py"

    def test_templates_have_test_file(self):
        """Test all templates include test file."""
        for template_type, files in TEMPLATES.items():
            test_files = [f for f in files if "test_" in f]
            assert len(test_files) == 1, f"{template_type} should have test file"


class TestSkbuildProjectGenerator:
    """Test SkbuildProjectGenerator class."""

    def test_invalid_template_type(self):
        """Test that invalid template type raises error."""
        with pytest.raises(ValueError, match="Invalid template type"):
            SkbuildProjectGenerator("myext", "invalid-type")

    def test_invalid_project_name(self):
        """Test that invalid project name raises error."""
        with pytest.raises(ValueError, match="Invalid project name"):
            SkbuildProjectGenerator("invalid-name", "skbuild-pybind11")

        with pytest.raises(ValueError, match="Invalid project name"):
            SkbuildProjectGenerator("123invalid", "skbuild-pybind11")

    def test_valid_project_names(self):
        """Test that valid project names are accepted."""
        # These should not raise
        SkbuildProjectGenerator("myext", "skbuild-pybind11")
        SkbuildProjectGenerator("my_ext", "skbuild-pybind11")
        SkbuildProjectGenerator("MyExt", "skbuild-pybind11")
        SkbuildProjectGenerator("ext123", "skbuild-pybind11")

    def test_get_description(self):
        """Test get_description returns correct description."""
        gen = SkbuildProjectGenerator("myext", "skbuild-pybind11")
        assert "pybind11" in gen.get_description()

    def test_invalid_env_tool(self):
        """Test that invalid env_tool raises error."""
        with pytest.raises(ValueError, match="Invalid env_tool"):
            SkbuildProjectGenerator("myext", "skbuild-pybind11", env_tool="invalid")

    def test_env_tool_uv_default(self, tmp_path):
        """Test that uv is the default env_tool."""
        gen = SkbuildProjectGenerator("myext", "skbuild-pybind11", tmp_path)
        gen.generate()
        makefile = (tmp_path / "Makefile").read_text()
        assert "uv sync" in makefile
        assert "uv sync --reinstall-package myext" in makefile
        assert "uv run pytest" in makefile

    def test_env_tool_venv(self, tmp_path):
        """Test venv env_tool generates pip/python Makefile."""
        gen = SkbuildProjectGenerator(
            "myext", "skbuild-pybind11", tmp_path, env_tool="venv"
        )
        gen.generate()
        makefile = (tmp_path / "Makefile").read_text()
        assert "PYTHON ?= python" in makefile
        assert "PIP ?= pip" in makefile
        assert "$(PIP) install" in makefile
        assert "$(PYTHON) -m pytest" in makefile
        assert "UV" not in makefile


class TestPybind11Generation:
    """Test pybind11 project generation."""

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create temporary output directory."""
        return tmp_path / "myext"

    def test_generates_all_files(self, output_dir):
        """Test that all expected files are generated."""
        gen = SkbuildProjectGenerator("myext", "skbuild-pybind11", output_dir)
        created = gen.generate()

        assert len(created) == 6
        assert (output_dir / "Makefile").exists()
        assert (output_dir / "pyproject.toml").exists()
        assert (output_dir / "CMakeLists.txt").exists()
        assert (output_dir / "src/myext/__init__.py").exists()
        assert (output_dir / "src/myext/_core.cpp").exists()
        assert (output_dir / "tests/test_myext.py").exists()

    def test_pyproject_content(self, output_dir):
        """Test pyproject.toml has correct content."""
        gen = SkbuildProjectGenerator("myext", "skbuild-pybind11", output_dir)
        gen.generate()

        content = (output_dir / "pyproject.toml").read_text()
        assert 'name = "myext"' in content
        assert "scikit-build-core" in content
        assert "pybind11" in content
        assert "scikit_build_core.build" in content

    def test_cmake_content(self, output_dir):
        """Test CMakeLists.txt has correct content."""
        gen = SkbuildProjectGenerator("myext", "skbuild-pybind11", output_dir)
        gen.generate()

        content = (output_dir / "CMakeLists.txt").read_text()
        assert "cmake_minimum_required" in content
        assert "find_package(pybind11" in content
        assert "pybind11_add_module" in content
        assert "src/myext/_core.cpp" in content

    def test_cpp_content(self, output_dir):
        """Test C++ source has correct content."""
        gen = SkbuildProjectGenerator("myext", "skbuild-pybind11", output_dir)
        gen.generate()

        content = (output_dir / "src/myext/_core.cpp").read_text()
        assert "#include <pybind11/pybind11.h>" in content
        assert "PYBIND11_MODULE" in content
        assert "add" in content
        assert "greet" in content

    def test_init_py_content(self, output_dir):
        """Test __init__.py has correct content."""
        gen = SkbuildProjectGenerator("myext", "skbuild-pybind11", output_dir)
        gen.generate()

        content = (output_dir / "src/myext/__init__.py").read_text()
        assert "from myext._core import add, greet" in content
        assert '__version__ = "0.1.0"' in content


class TestCythonGeneration:
    """Test Cython project generation."""

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create temporary output directory."""
        return tmp_path / "cyext"

    def test_generates_all_files(self, output_dir):
        """Test that all expected files are generated."""
        gen = SkbuildProjectGenerator("cyext", "skbuild-cython", output_dir)
        created = gen.generate()

        assert len(created) == 6
        assert (output_dir / "Makefile").exists()
        assert (output_dir / "pyproject.toml").exists()
        assert (output_dir / "CMakeLists.txt").exists()
        assert (output_dir / "src/cyext/__init__.py").exists()
        assert (output_dir / "src/cyext/_core.pyx").exists()
        assert (output_dir / "tests/test_cyext.py").exists()

    def test_pyproject_content(self, output_dir):
        """Test pyproject.toml has correct content."""
        gen = SkbuildProjectGenerator("cyext", "skbuild-cython", output_dir)
        gen.generate()

        content = (output_dir / "pyproject.toml").read_text()
        assert 'name = "cyext"' in content
        assert "scikit-build-core" in content
        assert "cython" in content

    def test_pyx_content(self, output_dir):
        """Test Cython source has correct content."""
        gen = SkbuildProjectGenerator("cyext", "skbuild-cython", output_dir)
        gen.generate()

        content = (output_dir / "src/cyext/_core.pyx").read_text()
        assert "cpdef int add" in content
        assert "cpdef str greet" in content


class TestCExtensionGeneration:
    """Test C extension project generation."""

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create temporary output directory."""
        return tmp_path / "cext"

    def test_generates_all_files(self, output_dir):
        """Test that all expected files are generated."""
        gen = SkbuildProjectGenerator("cext", "skbuild-c", output_dir)
        created = gen.generate()

        assert len(created) == 6
        assert (output_dir / "Makefile").exists()
        assert (output_dir / "pyproject.toml").exists()
        assert (output_dir / "CMakeLists.txt").exists()
        assert (output_dir / "src/cext/__init__.py").exists()
        assert (output_dir / "src/cext/_core.c").exists()
        assert (output_dir / "tests/test_cext.py").exists()

    def test_pyproject_content(self, output_dir):
        """Test pyproject.toml has correct content."""
        gen = SkbuildProjectGenerator("cext", "skbuild-c", output_dir)
        gen.generate()

        content = (output_dir / "pyproject.toml").read_text()
        assert 'name = "cext"' in content
        assert "scikit-build-core" in content
        # Should NOT have pybind11, cython, or nanobind
        assert "pybind11" not in content
        assert "cython" not in content
        assert "nanobind" not in content

    def test_c_content(self, output_dir):
        """Test C source has correct content."""
        gen = SkbuildProjectGenerator("cext", "skbuild-c", output_dir)
        gen.generate()

        content = (output_dir / "src/cext/_core.c").read_text()
        assert "#include <Python.h>" in content
        assert "PyInit__core" in content
        assert "cext_add" in content
        assert "cext_greet" in content


class TestNanobindGeneration:
    """Test nanobind project generation."""

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create temporary output directory."""
        return tmp_path / "nbext"

    def test_generates_all_files(self, output_dir):
        """Test that all expected files are generated."""
        gen = SkbuildProjectGenerator("nbext", "skbuild-nanobind", output_dir)
        created = gen.generate()

        assert len(created) == 6
        assert (output_dir / "Makefile").exists()
        assert (output_dir / "pyproject.toml").exists()
        assert (output_dir / "CMakeLists.txt").exists()
        assert (output_dir / "src/nbext/__init__.py").exists()
        assert (output_dir / "src/nbext/_core.cpp").exists()
        assert (output_dir / "tests/test_nbext.py").exists()

    def test_pyproject_content(self, output_dir):
        """Test pyproject.toml has correct content."""
        gen = SkbuildProjectGenerator("nbext", "skbuild-nanobind", output_dir)
        gen.generate()

        content = (output_dir / "pyproject.toml").read_text()
        assert 'name = "nbext"' in content
        assert "scikit-build-core" in content
        assert "nanobind" in content

    def test_cmake_content(self, output_dir):
        """Test CMakeLists.txt has correct content."""
        gen = SkbuildProjectGenerator("nbext", "skbuild-nanobind", output_dir)
        gen.generate()

        content = (output_dir / "CMakeLists.txt").read_text()
        assert "find_package(nanobind" in content
        assert "nanobind_add_module" in content

    def test_cpp_content(self, output_dir):
        """Test C++ source has correct content."""
        gen = SkbuildProjectGenerator("nbext", "skbuild-nanobind", output_dir)
        gen.generate()

        content = (output_dir / "src/nbext/_core.cpp").read_text()
        assert "#include <nanobind/nanobind.h>" in content
        assert "NB_MODULE" in content
        assert "add" in content
        assert "greet" in content
