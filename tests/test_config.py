"""Tests for user configuration loading and integration."""

import argparse
import textwrap

import pytest

from buildgen.common.config import (
    UserConfig,
    load_user_config,
)


class TestUserConfig:
    """Test UserConfig dataclass."""

    def test_defaults(self):
        cfg = UserConfig()
        assert cfg.user_name == ""
        assert cfg.user_email == ""
        assert cfg.defaults == {}

    def test_to_template_context(self):
        cfg = UserConfig(
            user_name="Alice",
            user_email="alice@example.com",
            defaults={"license": "MIT", "cxx_standard": 17},
        )
        ctx = cfg.to_template_context()
        assert ctx == {
            "user": {"name": "Alice", "email": "alice@example.com"},
            "defaults": {"license": "MIT", "cxx_standard": 17},
        }

    def test_to_template_context_empty(self):
        cfg = UserConfig()
        ctx = cfg.to_template_context()
        assert ctx == {
            "user": {"name": "", "email": ""},
            "defaults": {},
        }


class TestLoadUserConfig:
    """Test load_user_config function."""

    def test_load_missing_config(self, tmp_path):
        """Returns empty UserConfig when file doesn't exist."""
        cfg = load_user_config(tmp_path / "nonexistent.toml")
        assert cfg.user_name == ""
        assert cfg.user_email == ""
        assert cfg.defaults == {}

    def test_load_valid_config(self, tmp_path):
        """Parses both [user] and [defaults] sections correctly."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            textwrap.dedent("""\
            [user]
            name = "John Doe"
            email = "john@example.com"

            [defaults]
            license = "MIT"
            cxx_standard = 17
            env_tool = "uv"
        """)
        )

        cfg = load_user_config(config_file)
        assert cfg.user_name == "John Doe"
        assert cfg.user_email == "john@example.com"
        assert cfg.defaults == {
            "license": "MIT",
            "cxx_standard": 17,
            "env_tool": "uv",
        }

    def test_load_partial_config_user_only(self, tmp_path):
        """Handles config with only [user] section."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            textwrap.dedent("""\
            [user]
            name = "Jane"
        """)
        )

        cfg = load_user_config(config_file)
        assert cfg.user_name == "Jane"
        assert cfg.user_email == ""
        assert cfg.defaults == {}

    def test_load_partial_config_defaults_only(self, tmp_path):
        """Handles config with only [defaults] section."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            textwrap.dedent("""\
            [defaults]
            env_tool = "venv"
        """)
        )

        cfg = load_user_config(config_file)
        assert cfg.user_name == ""
        assert cfg.user_email == ""
        assert cfg.defaults == {"env_tool": "venv"}

    def test_load_empty_config(self, tmp_path):
        """Handles empty TOML file gracefully."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("")

        cfg = load_user_config(config_file)
        assert cfg.user_name == ""
        assert cfg.user_email == ""
        assert cfg.defaults == {}

    def test_load_malformed_config(self, tmp_path):
        """Returns empty UserConfig on malformed TOML."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("this is not valid toml [[[")

        cfg = load_user_config(config_file)
        assert cfg.user_name == ""
        assert cfg.user_email == ""
        assert cfg.defaults == {}


class TestUserConfigInLicenseTemplate:
    """Test that LICENSE.mako renders user.name when available."""

    def test_license_with_user_name(self, tmp_path):
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        user_cfg = UserConfig(user_name="Alice Smith")
        gen = SkbuildProjectGenerator(
            "myext", "skbuild-pybind11", tmp_path, user_config=user_cfg
        )
        gen.generate()

        content = (tmp_path / "LICENSE").read_text()
        assert "Alice Smith" in content
        assert "myext contributors" not in content
        assert "MIT License" in content

    def test_license_without_user_config(self, tmp_path):
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        gen = SkbuildProjectGenerator("myext", "skbuild-pybind11", tmp_path)
        gen.generate()

        content = (tmp_path / "LICENSE").read_text()
        assert "myext contributors" in content
        assert "MIT License" in content


class TestUserConfigInPyprojectTemplate:
    """Test that pyproject.toml renders authors when user info is present."""

    def test_pyproject_with_full_user(self, tmp_path):
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        user_cfg = UserConfig(user_name="Bob", user_email="bob@test.com")
        gen = SkbuildProjectGenerator(
            "myext", "skbuild-pybind11", tmp_path, user_config=user_cfg
        )
        gen.generate()

        content = (tmp_path / "pyproject.toml").read_text()
        assert "authors = [" in content
        assert 'name = "Bob"' in content
        assert 'email = "bob@test.com"' in content
        # Both fields should be in a single inline table
        for line in content.splitlines():
            if "authors" in line and "{" in line:
                break
            if 'name = "Bob"' in line and 'email = "bob@test.com"' in line:
                break
        else:
            # Check the block form: authors = [\n    { name = ..., email = ... }\n]
            authors_block = content.split("authors = [")[1].split("]")[0]
            assert 'name = "Bob"' in authors_block
            assert 'email = "bob@test.com"' in authors_block

    def test_pyproject_with_name_only(self, tmp_path):
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        user_cfg = UserConfig(user_name="Carol")
        gen = SkbuildProjectGenerator(
            "myext", "skbuild-pybind11", tmp_path, user_config=user_cfg
        )
        gen.generate()

        content = (tmp_path / "pyproject.toml").read_text()
        assert "authors = [" in content
        assert 'name = "Carol"' in content
        # email should not appear in the authors block
        authors_block = content.split("authors = [")[1].split("]")[0]
        assert "email" not in authors_block

    def test_pyproject_without_user_config(self, tmp_path):
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        gen = SkbuildProjectGenerator("myext", "skbuild-pybind11", tmp_path)
        gen.generate()

        content = (tmp_path / "pyproject.toml").read_text()
        assert "authors" not in content


class TestTemplatesWorkWithoutConfig:
    """Backward compatibility: all templates still render with empty user dict."""

    def test_skbuild_pybind11_no_config(self, tmp_path):
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        gen = SkbuildProjectGenerator("myext", "skbuild-pybind11", tmp_path)
        created = gen.generate()
        assert len(created) > 0
        assert (tmp_path / "pyproject.toml").exists()
        assert (tmp_path / "LICENSE").exists()

    def test_cmake_cpp_no_config(self, tmp_path):
        from buildgen.cmake.project_generator import CMakeProjectGenerator

        gen = CMakeProjectGenerator("myapp", "cpp/executable", tmp_path)
        created = gen.generate()
        assert len(created) > 0
        assert (tmp_path / "CMakeLists.txt").exists()


class TestCMakeProjectGeneratorContext:
    """Test that CMakeProjectGenerator passes context to templates."""

    def test_cmake_with_user_config(self, tmp_path):
        from buildgen.cmake.project_generator import CMakeProjectGenerator

        user_cfg = UserConfig(user_name="Dave")
        gen = CMakeProjectGenerator(
            "myapp", "cpp/executable", tmp_path, user_config=user_cfg
        )
        # Should not raise during generation
        created = gen.generate()
        assert len(created) > 0


class TestConfigCLICommands:
    """Test buildgen config init/show/path commands."""

    def test_config_init_creates_file(self, tmp_path, monkeypatch):
        from buildgen.cli.commands import cmd_config_init
        import buildgen.common.config as config_mod

        config_path = tmp_path / "config.toml"
        monkeypatch.setattr(config_mod, "DEFAULT_CONFIG_PATH", config_path)

        args = argparse.Namespace()
        cmd_config_init(args)

        assert config_path.exists()
        content = config_path.read_text()
        assert "[user]" in content
        assert "[defaults]" in content

    def test_config_init_no_overwrite(self, tmp_path, monkeypatch):
        from buildgen.cli.commands import cmd_config_init
        import buildgen.common.config as config_mod

        config_path = tmp_path / "config.toml"
        config_path.write_text("existing content")
        monkeypatch.setattr(config_mod, "DEFAULT_CONFIG_PATH", config_path)

        args = argparse.Namespace()
        with pytest.raises(SystemExit):
            cmd_config_init(args)

        # Content should be unchanged
        assert config_path.read_text() == "existing content"

    def test_config_show_no_file(self, tmp_path, monkeypatch, capsys):
        from buildgen.cli.commands import cmd_config_show
        import buildgen.common.config as config_mod

        config_path = tmp_path / "nonexistent.toml"
        monkeypatch.setattr(config_mod, "DEFAULT_CONFIG_PATH", config_path)

        args = argparse.Namespace()
        cmd_config_show(args)

        output = capsys.readouterr().out
        assert "No config file found" in output

    def test_config_show_with_file(self, tmp_path, monkeypatch, capsys):
        from buildgen.cli.commands import cmd_config_show
        import buildgen.common.config as config_mod

        config_path = tmp_path / "config.toml"
        config_path.write_text(
            textwrap.dedent("""\
            [user]
            name = "Tester"
            email = "test@test.com"

            [defaults]
            env_tool = "venv"
        """)
        )
        monkeypatch.setattr(config_mod, "DEFAULT_CONFIG_PATH", config_path)

        args = argparse.Namespace()
        cmd_config_show(args)

        output = capsys.readouterr().out
        assert "'Tester'" in output
        assert "'test@test.com'" in output
        assert "'venv'" in output

    def test_config_path(self, capsys):
        from buildgen.cli.commands import cmd_config_path

        args = argparse.Namespace()
        cmd_config_path(args)

        output = capsys.readouterr().out.strip()
        assert ".buildgen/config.toml" in output


class TestDefaultsAppliedToEnvTool:
    """Test that defaults.env_tool is used as fallback in cmd_new."""

    def test_defaults_env_tool_used_when_not_explicit(self, tmp_path, monkeypatch):
        """When --env is not passed (None), fall back to user config default."""
        import buildgen.common.config as config_mod

        config_path = tmp_path / "config.toml"
        config_path.write_text(
            textwrap.dedent("""\
            [defaults]
            env_tool = "venv"
        """)
        )
        monkeypatch.setattr(config_mod, "DEFAULT_CONFIG_PATH", config_path)

        from buildgen.cli.commands import cmd_new

        output_dir = tmp_path / "proj"
        args = argparse.Namespace(
            name="testproj",
            recipe="py/pybind11",
            output=str(output_dir),
            env=None,  # argparse default when --env not passed
        )
        cmd_new(args)

        makefile = (output_dir / "Makefile").read_text()
        assert "PIP ?= pip" in makefile

    def test_explicit_env_overrides_config(self, tmp_path, monkeypatch):
        """When --env uv is explicitly passed, it should override config default."""
        import buildgen.common.config as config_mod

        config_path = tmp_path / "config.toml"
        config_path.write_text(
            textwrap.dedent("""\
            [defaults]
            env_tool = "venv"
        """)
        )
        monkeypatch.setattr(config_mod, "DEFAULT_CONFIG_PATH", config_path)

        from buildgen.cli.commands import cmd_new

        output_dir = tmp_path / "proj"
        args = argparse.Namespace(
            name="testproj",
            recipe="py/pybind11",
            output=str(output_dir),
            env="uv",  # explicitly passed --env uv
        )
        cmd_new(args)

        makefile = (output_dir / "Makefile").read_text()
        assert "uv sync" in makefile


class TestDefaultsCxxStandard:
    """Test that defaults.cxx_standard flows through to C++ CMakeLists.txt."""

    def test_cpp_cxx_standard_from_config(self, tmp_path):
        from buildgen.cmake.project_generator import CMakeProjectGenerator
        from buildgen.common.config import UserConfig

        user_cfg = UserConfig(defaults={"cxx_standard": 20})
        gen = CMakeProjectGenerator(
            "myapp", "cpp/executable", tmp_path, user_config=user_cfg
        )
        gen.generate()

        content = (tmp_path / "CMakeLists.txt").read_text()
        assert "CMAKE_CXX_STANDARD 20" in content
        assert "CMAKE_CXX_STANDARD 17" not in content

    def test_cpp_cxx_standard_default(self, tmp_path):
        from buildgen.cmake.project_generator import CMakeProjectGenerator

        gen = CMakeProjectGenerator("myapp", "cpp/executable", tmp_path)
        gen.generate()

        content = (tmp_path / "CMakeLists.txt").read_text()
        assert "CMAKE_CXX_STANDARD 17" in content

    def test_skbuild_cxx_standard_from_config(self, tmp_path):
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        user_cfg = UserConfig(defaults={"cxx_standard": 20})
        gen = SkbuildProjectGenerator(
            "myext", "skbuild-pybind11", tmp_path, user_config=user_cfg
        )
        gen.generate()

        content = (tmp_path / "CMakeLists.txt").read_text()
        assert "CMAKE_CXX_STANDARD 20" in content


class TestDefaultsCStandard:
    """Test that defaults.c_standard flows through to C CMakeLists.txt."""

    def test_c_standard_from_config(self, tmp_path):
        from buildgen.cmake.project_generator import CMakeProjectGenerator
        from buildgen.common.config import UserConfig

        user_cfg = UserConfig(defaults={"c_standard": 17})
        gen = CMakeProjectGenerator(
            "myapp", "c/executable", tmp_path, user_config=user_cfg
        )
        gen.generate()

        content = (tmp_path / "CMakeLists.txt").read_text()
        assert "CMAKE_C_STANDARD 17" in content
        assert "CMAKE_C_STANDARD 11" not in content

    def test_c_standard_default(self, tmp_path):
        from buildgen.cmake.project_generator import CMakeProjectGenerator

        gen = CMakeProjectGenerator("myapp", "c/executable", tmp_path)
        gen.generate()

        content = (tmp_path / "CMakeLists.txt").read_text()
        assert "CMAKE_C_STANDARD 11" in content


class TestDefaultsLicenseAndPython:
    """Test that defaults.license and defaults.python_version flow through."""

    def test_license_from_config(self, tmp_path):
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        user_cfg = UserConfig(defaults={"license": "Apache-2.0"})
        gen = SkbuildProjectGenerator(
            "myext", "skbuild-pybind11", tmp_path, user_config=user_cfg
        )
        gen.generate()

        content = (tmp_path / "pyproject.toml").read_text()
        assert 'license = { text = "Apache-2.0" }' in content
        # LICENSE file body should also be Apache
        license_body = (tmp_path / "LICENSE").read_text()
        assert "Apache License" in license_body
        assert "MIT License" not in license_body

    def test_license_default(self, tmp_path):
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        gen = SkbuildProjectGenerator("myext", "skbuild-pybind11", tmp_path)
        gen.generate()

        content = (tmp_path / "pyproject.toml").read_text()
        assert 'license = { text = "MIT" }' in content
        # LICENSE file body should be MIT
        license_body = (tmp_path / "LICENSE").read_text()
        assert "MIT License" in license_body

    def test_python_version_from_config(self, tmp_path):
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        user_cfg = UserConfig(defaults={"python_version": "3.12"})
        gen = SkbuildProjectGenerator(
            "myext", "skbuild-pybind11", tmp_path, user_config=user_cfg
        )
        gen.generate()

        content = (tmp_path / "pyproject.toml").read_text()
        assert 'requires-python = ">=3.12"' in content

    def test_python_version_default(self, tmp_path):
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        gen = SkbuildProjectGenerator("myext", "skbuild-pybind11", tmp_path)
        gen.generate()

        content = (tmp_path / "pyproject.toml").read_text()
        assert 'requires-python = ">=3.10"' in content


class TestLicenseBodyMatchesConfig:
    """Test that LICENSE file body matches the configured defaults.license."""

    def _generate_license(self, tmp_path, license_id):
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        user_cfg = UserConfig(
            user_name="Test Author", defaults={"license": license_id}
        )
        gen = SkbuildProjectGenerator(
            "myext", "skbuild-pybind11", tmp_path, user_config=user_cfg
        )
        gen.generate()
        return (tmp_path / "LICENSE").read_text()

    def test_mit_body(self, tmp_path):
        content = self._generate_license(tmp_path, "MIT")
        assert "MIT License" in content
        assert "Permission is hereby granted" in content
        assert "Test Author" in content

    def test_bsd_2_clause_body(self, tmp_path):
        content = self._generate_license(tmp_path, "BSD-2-Clause")
        assert "BSD 2-Clause License" in content
        assert "Redistribution and use" in content
        assert "Test Author" in content
        assert "MIT License" not in content

    def test_bsd_3_clause_body(self, tmp_path):
        content = self._generate_license(tmp_path, "BSD-3-Clause")
        assert "BSD 3-Clause License" in content
        assert "Neither the name of the copyright holder" in content
        assert "Test Author" in content
        assert "MIT License" not in content

    def test_isc_body(self, tmp_path):
        content = self._generate_license(tmp_path, "ISC")
        assert "ISC License" in content
        assert "Permission to use, copy, modify" in content
        assert "Test Author" in content
        assert "MIT License" not in content

    def test_apache_2_body(self, tmp_path):
        content = self._generate_license(tmp_path, "Apache-2.0")
        assert "Apache License" in content
        assert "Version 2.0" in content
        assert "Test Author" in content
        assert "MIT License" not in content

    def test_unknown_license_fallback(self, tmp_path):
        content = self._generate_license(tmp_path, "LGPL-3.0-only")
        assert "LGPL-3.0-only" in content
        assert "Test Author" in content
        assert "spdx.org/licenses/LGPL-3.0-only" in content
        assert "MIT License" not in content
