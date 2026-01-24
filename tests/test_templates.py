"""Tests for template resolver and override system."""

import pytest
from pathlib import Path

from buildgen.templates.resolver import (
    BUILTIN_TEMPLATES_DIR,
    TemplateResolver,
    copy_templates,
    get_builtin_template_types,
    get_builtin_template_recipes,
)
from buildgen.skbuild.templates import (
    SKBUILD_TYPES,
    TEMPLATES_DIR,
    resolve_template_files,
    LEGACY_TO_RECIPE_PATH,
)


class TestBuiltinTemplates:
    """Test built-in template structure."""

    def test_builtin_templates_dir_exists(self):
        """Test that built-in templates directory exists."""
        assert BUILTIN_TEMPLATES_DIR.exists()
        assert BUILTIN_TEMPLATES_DIR.is_dir()

    def test_skbuild_templates_dir_exists(self):
        """Test that skbuild templates directory exists."""
        assert TEMPLATES_DIR.exists()
        assert TEMPLATES_DIR.is_dir()

    def test_get_builtin_template_recipes(self):
        """Test getting available template recipes."""
        recipes = get_builtin_template_recipes()
        # Should use new recipe paths
        assert "py/pybind11" in recipes
        assert "py/cython" in recipes
        assert "py/cext" in recipes
        assert "py/nanobind" in recipes
        # Common should not be in the list
        assert "common" not in recipes

    def test_get_builtin_template_types(self):
        """Test getting available template types (legacy)."""
        types = get_builtin_template_types()
        # Should return same as recipes
        assert types == get_builtin_template_recipes()


class TestTemplateResolver:
    """Test TemplateResolver class."""

    def test_resolve_builtin_template(self):
        """Test resolving a built-in template."""
        resolver = TemplateResolver()
        # Use new recipe path
        path, source = resolver.resolve("py/pybind11", "pyproject.toml.mako")
        assert path.exists()
        assert source == "built-in"
        assert "pyproject.toml.mako" in str(path)

    def test_resolve_common_template(self):
        """Test resolving a common template."""
        resolver = TemplateResolver()
        path, source = resolver.resolve_common("Makefile.uv.mako")
        assert path.exists()
        assert source == "built-in"
        assert "Makefile.uv.mako" in str(path)

    def test_resolve_not_found(self):
        """Test resolving non-existent template raises error."""
        resolver = TemplateResolver()
        with pytest.raises(FileNotFoundError):
            resolver.resolve("py/pybind11", "nonexistent.mako")

    def test_resolve_common_not_found(self):
        """Test resolving non-existent common template raises error."""
        resolver = TemplateResolver()
        with pytest.raises(FileNotFoundError):
            resolver.resolve_common("nonexistent.mako")

    def test_local_override(self, tmp_path):
        """Test local override takes precedence."""
        # Create local override with recipe path
        override_dir = tmp_path / ".buildgen/templates/py/pybind11"
        override_dir.mkdir(parents=True)
        override_file = override_dir / "pyproject.toml.mako"
        override_file.write_text("# Local override")

        resolver = TemplateResolver(tmp_path)
        path, source = resolver.resolve("py/pybind11", "pyproject.toml.mako")
        assert path == override_file
        assert source == "local"

    def test_global_override(self, tmp_path, monkeypatch):
        """Test global override takes precedence over built-in."""
        # Create a fake home directory
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Create global override with recipe path
        override_dir = fake_home / ".buildgen/templates/py/pybind11"
        override_dir.mkdir(parents=True)
        override_file = override_dir / "pyproject.toml.mako"
        override_file.write_text("# Global override")

        resolver = TemplateResolver()
        path, source = resolver.resolve("py/pybind11", "pyproject.toml.mako")
        assert path == override_file
        assert source == "global"

    def test_env_override(self, tmp_path, monkeypatch):
        """Test environment variable override takes precedence."""
        # Create env override with recipe path
        env_dir = tmp_path / "env_templates/py/pybind11"
        env_dir.mkdir(parents=True)
        env_file = env_dir / "pyproject.toml.mako"
        env_file.write_text("# Env override")

        monkeypatch.setenv("BUILDGEN_TEMPLATES", str(tmp_path / "env_templates"))

        resolver = TemplateResolver()
        path, source = resolver.resolve("py/pybind11", "pyproject.toml.mako")
        assert path == env_file
        assert source == "env"

    def test_env_override_priority(self, tmp_path, monkeypatch):
        """Test env override takes priority over local override."""
        # Create local override
        local_dir = tmp_path / ".buildgen/templates/py/pybind11"
        local_dir.mkdir(parents=True)
        local_file = local_dir / "pyproject.toml.mako"
        local_file.write_text("# Local override")

        # Create env override
        env_dir = tmp_path / "env_templates/py/pybind11"
        env_dir.mkdir(parents=True)
        env_file = env_dir / "pyproject.toml.mako"
        env_file.write_text("# Env override")

        monkeypatch.setenv("BUILDGEN_TEMPLATES", str(tmp_path / "env_templates"))

        resolver = TemplateResolver(tmp_path)
        path, source = resolver.resolve("py/pybind11", "pyproject.toml.mako")
        assert path == env_file
        assert source == "env"

    def test_list_overrides(self, tmp_path):
        """Test listing override files."""
        # Create local override with recipe path
        override_dir = tmp_path / ".buildgen/templates/py/pybind11"
        override_dir.mkdir(parents=True)
        (override_dir / "pyproject.toml.mako").write_text("# Override")

        resolver = TemplateResolver(tmp_path)
        overrides = resolver.list_overrides("py/pybind11")
        assert "pyproject.toml.mako" in overrides
        assert overrides["pyproject.toml.mako"] == "local"

    def test_list_overrides_empty(self, tmp_path):
        """Test listing overrides when none exist."""
        resolver = TemplateResolver(tmp_path)
        overrides = resolver.list_overrides("py/pybind11")
        assert overrides == {}


class TestCopyTemplates:
    """Test copy_templates function."""

    def test_copy_templates(self, tmp_path):
        """Test copying templates to destination."""
        dest_dir = tmp_path / "dest"
        # Use recipe path
        copied = copy_templates("py/pybind11", dest_dir)

        # Should have type-specific files + common files
        assert len(copied) > 0

        # Check type-specific files (now in py/pybind11/)
        assert (dest_dir / "py/pybind11/pyproject.toml.mako").exists()
        assert (dest_dir / "py/pybind11/CMakeLists.txt.mako").exists()

        # Check common files
        assert (dest_dir / "common/Makefile.uv.mako").exists()
        assert (dest_dir / "common/Makefile.venv.mako").exists()

    def test_copy_templates_without_common(self, tmp_path):
        """Test copying templates without common files."""
        dest_dir = tmp_path / "dest"
        copy_templates("py/pybind11", dest_dir, include_common=False)

        # Check type-specific files
        assert (dest_dir / "py/pybind11/pyproject.toml.mako").exists()

        # Common files should not exist
        assert not (dest_dir / "common").exists()

    def test_copy_templates_invalid_type(self, tmp_path):
        """Test copying invalid template type raises error."""
        dest_dir = tmp_path / "dest"
        with pytest.raises(ValueError, match="Recipe template not found"):
            copy_templates("nonexistent", dest_dir)


class TestResolveTemplateFiles:
    """Test resolve_template_files function."""

    def test_resolve_all_files(self):
        """Test resolving all files for a template type."""
        # resolve_template_files still uses legacy type names internally
        resolved = resolve_template_files("skbuild-pybind11")

        # Should have 13 files
        assert len(resolved) == 13

        # Check expected output paths
        assert ".gitignore" in resolved
        assert ".github/workflows/ci.yml" in resolved
        assert ".github/workflows/build-publish.yml" in resolved
        assert "CHANGELOG.md" in resolved
        assert "LICENSE" in resolved
        assert "Makefile" in resolved
        assert "pyproject.toml" in resolved
        assert "README.md" in resolved
        assert "CMakeLists.txt" in resolved
        assert "src/${name}/py.typed" in resolved

        # All should be built-in
        for path, source in resolved.values():
            assert source == "built-in"
            assert path.exists()

    def test_resolve_with_venv_env_tool(self):
        """Test resolving with venv environment tool."""
        resolved = resolve_template_files("skbuild-pybind11", env_tool="venv")

        makefile_path, source = resolved["Makefile"]
        assert "venv" in str(makefile_path)

    def test_resolve_with_local_override(self, tmp_path):
        """Test resolving with local override."""
        # Create local override using recipe path
        override_dir = tmp_path / ".buildgen/templates/py/pybind11"
        override_dir.mkdir(parents=True)
        (override_dir / "pyproject.toml.mako").write_text("# Override")

        resolved = resolve_template_files("skbuild-pybind11", project_dir=tmp_path)

        # pyproject.toml should be from local override
        path, source = resolved["pyproject.toml"]
        assert source == "local"

        # Other files should be built-in
        makefile_path, makefile_source = resolved["Makefile"]
        assert makefile_source == "built-in"

    def test_resolve_invalid_type(self):
        """Test resolving invalid template type raises error."""
        with pytest.raises(ValueError, match="Unknown template type"):
            resolve_template_files("nonexistent")


class TestSkbuildTypes:
    """Test SKBUILD_TYPES constant."""

    def test_all_types_defined(self):
        """Test all expected types are defined."""
        assert "skbuild-pybind11" in SKBUILD_TYPES
        assert "skbuild-cython" in SKBUILD_TYPES
        assert "skbuild-c" in SKBUILD_TYPES
        assert "skbuild-nanobind" in SKBUILD_TYPES

    def test_types_have_descriptions(self):
        """Test all types have non-empty descriptions."""
        for name, description in SKBUILD_TYPES.items():
            assert description
            assert len(description) > 10

    def test_legacy_to_recipe_mapping(self):
        """Test legacy type to recipe path mapping."""
        assert LEGACY_TO_RECIPE_PATH["skbuild-pybind11"] == "py/pybind11"
        assert LEGACY_TO_RECIPE_PATH["skbuild-cython"] == "py/cython"
        assert LEGACY_TO_RECIPE_PATH["skbuild-c"] == "py/cext"
        assert LEGACY_TO_RECIPE_PATH["skbuild-nanobind"] == "py/nanobind"
