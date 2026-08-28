"""Tests for scikit-build-core project generation."""

import argparse

import pytest

from buildgen.cli import cmd_new, cmd_render
from buildgen.skbuild.generator import (
    SkbuildProjectGenerator,
    get_skbuild_types,
    is_skbuild_type,
)
from buildgen.skbuild.templates import (
    PY_PLAIN_TYPES,
    SKBUILD_TYPES,
    TEMPLATE_FILES,
    get_type_description,
)


class TestSkbuildTypes:
    """Test skbuild type utilities."""

    def test_get_skbuild_types(self):
        """Test get_skbuild_types returns all types."""
        types = get_skbuild_types()
        assert "skbuild-pybind11" in types
        assert "skbuild-pybind11-flex" in types
        assert "skbuild-cython" in types
        assert "skbuild-c" in types
        assert "skbuild-nanobind" in types
        assert len(types) == 5

    def test_is_skbuild_type(self):
        """Test is_skbuild_type detection."""
        assert is_skbuild_type("skbuild-pybind11")
        assert is_skbuild_type("skbuild-pybind11-flex")
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
            assert template_type in TEMPLATE_FILES

    def test_all_plain_types_have_templates(self):
        """Test all PY_PLAIN_TYPES have corresponding templates."""
        for template_type in PY_PLAIN_TYPES:
            assert template_type in TEMPLATE_FILES

    def test_types_are_registered_exactly_once(self):
        """Every TEMPLATE_FILES key is described by exactly one registry."""
        assert set(TEMPLATE_FILES) == set(SKBUILD_TYPES) | set(PY_PLAIN_TYPES)
        assert not set(SKBUILD_TYPES) & set(PY_PLAIN_TYPES)
        for template_type in TEMPLATE_FILES:
            assert get_type_description(template_type) != "Unknown template type"

    def test_templates_have_required_files(self):
        """Test all templates include required files."""
        required_files = ["Makefile", "pyproject.toml"]
        for template_type, files in TEMPLATE_FILES.items():
            for required in required_files:
                assert required in files, f"{template_type} missing {required}"

    def test_native_templates_have_cmakelists(self):
        """Native (scikit-build-core) templates drive a CMake build."""
        for template_type in SKBUILD_TYPES:
            assert "CMakeLists.txt" in TEMPLATE_FILES[template_type], (
                f"{template_type} missing CMakeLists.txt"
            )

    def test_plain_templates_have_no_cmakelists(self):
        """Pure-Python templates must not emit a CMake build."""
        for template_type in PY_PLAIN_TYPES:
            assert "CMakeLists.txt" not in TEMPLATE_FILES[template_type]

    def test_native_templates_have_source_files(self):
        """Test all native templates include an extension source file."""
        for template_type in SKBUILD_TYPES:
            files = TEMPLATE_FILES[template_type]
            source_files = [f for f in files if "/_core." in f]
            assert len(source_files) == 1, (
                f"{template_type} should have one _core source file"
            )

    def test_plain_templates_have_python_module(self):
        """Pure-Python templates ship a plain .py module, not an extension."""
        for template_type in PY_PLAIN_TYPES:
            files = TEMPLATE_FILES[template_type]
            assert not [f for f in files if "/_core." in f]
            modules = [f for f in files if f.endswith(".py") and "__init__" not in f]
            assert modules, f"{template_type} should ship a Python module"

    def test_templates_have_init_py(self):
        """Test all templates include __init__.py."""
        for template_type, files in TEMPLATE_FILES.items():
            init_files = [f for f in files if "__init__.py" in f]
            assert len(init_files) == 1, f"{template_type} should have __init__.py"

    def test_templates_have_test_file(self):
        """Test all templates include test file."""
        for template_type, files in TEMPLATE_FILES.items():
            test_files = [f for f in files if f.startswith("tests/")]
            assert test_files, f"{template_type} should have at least one test file"


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

        assert len(created) == 13
        assert (output_dir / ".gitignore").exists()
        assert (output_dir / "Makefile").exists()
        assert (output_dir / "pyproject.toml").exists()
        assert (output_dir / "README.md").exists()
        assert (output_dir / "CHANGELOG.md").exists()
        assert (output_dir / "CMakeLists.txt").exists()
        assert (output_dir / "src/myext/__init__.py").exists()
        assert (output_dir / "src/myext/_core.cpp").exists()
        assert (output_dir / "src/myext/py.typed").exists()
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


class TestPybind11FlexGeneration:
    """Test pybind11-flex project generation."""

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Temporary output directory."""
        return tmp_path / "flexext"

    def test_generates_configurable_files(self, output_dir):
        """Test that all expected files exist."""
        gen = SkbuildProjectGenerator("flexext", "skbuild-pybind11-flex", output_dir)
        created = gen.generate()

        expected = {
            output_dir / "Makefile",
            output_dir / "pyproject.toml",
            output_dir / "CMakeLists.txt",
            output_dir / "project.flex.json",
            output_dir / "src/flexext/__init__.py",
            output_dir / "src/flexext/_core.cpp",
            output_dir / "examples/cli/main.cpp",
            output_dir / "tests/test_flexext.py",
            output_dir / "tests/native/test_module.catch2.cpp",
            output_dir / "tests/native/test_module.gtest.cpp",
        }
        assert expected.issubset(set(created))

    def test_cmake_content_has_options(self, output_dir):
        """Test that CMakeLists.txt exposes configuration toggles."""
        gen = SkbuildProjectGenerator("flexext", "skbuild-pybind11-flex", output_dir)
        gen.generate()
        content = (output_dir / "CMakeLists.txt").read_text()
        assert "BUILD_CPP_TESTS" in content
        assert "TEST_FRAMEWORK" in content
        assert "BUILD_EMBEDDED_CLI" in content
        assert "FetchContent_Declare" in content

    def test_project_config_mentions_options(self, output_dir):
        """Ensure the config example documents options."""
        gen = SkbuildProjectGenerator("flexext", "skbuild-pybind11-flex", output_dir)
        gen.generate()
        content = (output_dir / "project.flex.json").read_text()
        assert '"options"' in content
        assert '"test_framework"' in content
        assert '"cmake_options"' in content


class TestConfigurableWorkflow:
    """End-to-end configurable recipe workflow."""

    def test_new_emits_config_only(self, tmp_path):
        """buildgen new should only create config for configurable recipes."""
        project_dir = tmp_path / "flexcfg"
        args = argparse.Namespace(
            name="flexcfg", recipe="py/pybind11-flex", output=str(project_dir), env="uv"
        )
        cmd_new(args)

        config_path = project_dir / "project.flex.json"
        assert config_path.exists()
        assert not (project_dir / "CMakeLists.txt").exists()

    def test_render_respects_options(self, tmp_path):
        """buildgen render should honor edited options."""
        config_dir = tmp_path / "flexrender"
        args = argparse.Namespace(
            name="flexproj",
            recipe="py/pybind11-flex",
            output=str(config_dir),
            env="uv",
        )
        cmd_new(args)
        config_path = config_dir / "project.flex.json"

        text = config_path.read_text()
        text = text.replace('"test_framework": "catch2"', '"test_framework": "gtest"')
        text = text.replace('"build_examples": false', '"build_examples": true')
        text = text.replace('"env": "uv"', '"env": "venv"')
        config_path.write_text(text)

        output_dir = tmp_path / "rendered"
        render_args = argparse.Namespace(
            config=str(config_path), output=str(output_dir), env=None
        )
        cmd_render(render_args)

        pyproject = (output_dir / "pyproject.toml").read_text()
        assert 'TEST_FRAMEWORK = "gtest"' in pyproject
        assert "BUILD_EMBEDDED_CLI = true" in pyproject

        cmake = (output_dir / "CMakeLists.txt").read_text()
        assert 'set(TEST_FRAMEWORK "gtest"' in cmake

        makefile = (output_dir / "Makefile").read_text()
        assert "PIP ?= pip" in makefile  # indicates venv Makefile
        assert "UV" not in makefile

        assert (output_dir / "examples/cli/main.cpp").exists()
        rendered_config = (output_dir / "project.json").read_text()
        assert "<options" not in rendered_config
        assert "-DTEST_FRAMEWORK=gtest" in rendered_config


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

        assert len(created) == 13
        assert (output_dir / ".gitignore").exists()
        assert (output_dir / "Makefile").exists()
        assert (output_dir / "pyproject.toml").exists()
        assert (output_dir / "README.md").exists()
        assert (output_dir / "CHANGELOG.md").exists()
        assert (output_dir / "CMakeLists.txt").exists()
        assert (output_dir / "src/cyext/__init__.py").exists()
        assert (output_dir / "src/cyext/_core.pyx").exists()
        assert (output_dir / "src/cyext/py.typed").exists()
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

        assert len(created) == 13
        assert (output_dir / ".gitignore").exists()
        assert (output_dir / "Makefile").exists()
        assert (output_dir / "pyproject.toml").exists()
        assert (output_dir / "README.md").exists()
        assert (output_dir / "CHANGELOG.md").exists()
        assert (output_dir / "CMakeLists.txt").exists()
        assert (output_dir / "src/cext/__init__.py").exists()
        assert (output_dir / "src/cext/_core.c").exists()
        assert (output_dir / "src/cext/py.typed").exists()
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

        assert len(created) == 13
        assert (output_dir / ".gitignore").exists()
        assert (output_dir / "Makefile").exists()
        assert (output_dir / "pyproject.toml").exists()
        assert (output_dir / "README.md").exists()
        assert (output_dir / "CHANGELOG.md").exists()
        assert (output_dir / "CMakeLists.txt").exists()
        assert (output_dir / "src/nbext/__init__.py").exists()
        assert (output_dir / "src/nbext/_core.cpp").exists()
        assert (output_dir / "src/nbext/py.typed").exists()
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


class TestNodepsRecipe:
    """Test the pure-Python py/nodeps recipe."""

    def test_recipe_registration(self):
        """py/nodeps is registered as a non-native Python recipe."""
        from buildgen.recipes import get_recipe

        recipe = get_recipe("py/nodeps")
        assert recipe.build_system == "python"
        assert recipe.language == "python"
        assert recipe.framework is None
        assert recipe.template_type == "py/nodeps"
        assert not recipe.configurable
        assert recipe.default_options["pure_python"] is True

    def test_template_type_defaults_to_framework(self):
        """Native recipes keep the legacy skbuild-{framework} template key."""
        from buildgen.recipes import get_recipe

        assert get_recipe("py/pybind11").template_type == "skbuild-pybind11"
        assert get_recipe("py/cext").template_type == "skbuild-c"

    def test_not_a_skbuild_type(self):
        """py/nodeps must not leak into the scikit-build registry."""
        assert not is_skbuild_type("py/nodeps")
        assert "py/nodeps" not in SKBUILD_TYPES
        assert "py/nodeps" in PY_PLAIN_TYPES
        assert get_type_description("py/nodeps")

    def test_cmd_new_generates_pure_python_project(self, tmp_path):
        """buildgen new -r py/nodeps renders a complete pure-Python project."""
        project_dir = tmp_path / "nodepsproj"
        args = argparse.Namespace(
            name="nodepsproj",
            recipe="py/nodeps",
            output=str(project_dir),
            env="uv",
            no_update_deps=True,
        )
        cmd_new(args)

        for expected in (
            "pyproject.toml",
            "Makefile",
            "README.md",
            "CHANGELOG.md",
            "LICENSE",
            ".gitignore",
            ".github/workflows/ci.yml",
            ".github/workflows/publish.yml",
            "src/nodepsproj/__init__.py",
            "src/nodepsproj/core.py",
            "src/nodepsproj/py.typed",
            "tests/test_nodepsproj.py",
        ):
            assert (project_dir / expected).exists(), f"missing {expected}"

        assert not (project_dir / "CMakeLists.txt").exists()

    def test_generated_pyproject_declares_no_dependencies(self, tmp_path):
        """The generated distribution has an empty runtime dependency list."""
        project_dir = tmp_path / "nodepsproj"
        gen = SkbuildProjectGenerator(
            "nodepsproj",
            "py/nodeps",
            project_dir,
            context={"options": {"pure_python": True}},
            update_deps=False,
        )
        gen.generate()

        pyproject = (project_dir / "pyproject.toml").read_text()
        assert "dependencies = []" in pyproject
        assert 'build-backend = "uv_build"' in pyproject
        assert "[tool.uv.build-backend]" in pyproject
        assert "scikit_build_core" not in pyproject
        assert "[tool.scikit-build]" not in pyproject

    def test_generated_module_imports_stdlib_only(self, tmp_path):
        """The example module must not import third-party packages."""
        project_dir = tmp_path / "nodepsproj"
        gen = SkbuildProjectGenerator(
            "nodepsproj", "py/nodeps", project_dir, update_deps=False
        )
        gen.generate()

        core = (project_dir / "src/nodepsproj/core.py").read_text()
        imports = [
            line
            for line in core.splitlines()
            if line.startswith(("import ", "from ")) and "__future__" not in line
        ]
        assert not imports, f"unexpected imports: {imports}"

    def test_description(self, tmp_path):
        """The generator reports a description for the plain recipe."""
        gen = SkbuildProjectGenerator(
            "nodepsproj", "py/nodeps", tmp_path / "x", update_deps=False
        )
        assert gen.get_description() == PY_PLAIN_TYPES["py/nodeps"]
