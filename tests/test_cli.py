"""CLI tests to ensure buildgen can be imported and run."""

import subprocess
import sys

import pytest


class TestCLIImport:
    """Test that CLI modules can be imported without errors."""

    def test_import_buildgen(self):
        """Test that the main buildgen package can be imported."""
        import buildgen

        assert hasattr(buildgen, "__version__")

    def test_import_cli(self):
        """Test that the CLI module can be imported."""
        from buildgen import cli

        assert hasattr(cli, "main")
        assert hasattr(cli, "create_parser")

    def test_import_makefile_variables(self):
        """Test that makefile variables module can be imported."""
        from buildgen.makefile import variables

        assert hasattr(variables, "get_make_version")
        version = variables.get_make_version()
        assert isinstance(version, float)
        assert version > 0

    def test_import_makefile_generator(self):
        """Test that makefile generator can be imported."""
        from buildgen.makefile import generator

        assert hasattr(generator, "MakefileGenerator")


class TestCLIExecution:
    """Test CLI execution via subprocess."""

    def test_cli_help(self):
        """Test that --help works."""
        result = subprocess.run(
            [sys.executable, "-m", "buildgen", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "buildgen" in result.stdout
        assert "Build system generator" in result.stdout

    def test_cli_version(self):
        """Test that --version works."""
        result = subprocess.run(
            [sys.executable, "-m", "buildgen", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "buildgen" in result.stdout

    def test_cli_list(self):
        """Test that 'list' command works."""
        result = subprocess.run(
            [sys.executable, "-m", "buildgen", "list"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Available recipes" in result.stdout

    def test_cli_no_command_shows_help(self):
        """Test that running without a command shows help."""
        result = subprocess.run(
            [sys.executable, "-m", "buildgen"],
            capture_output=True,
            text=True,
        )
        # Exit code 1 is expected when no command given
        assert result.returncode == 1
        assert "usage:" in result.stdout.lower() or "usage:" in result.stderr.lower()


class TestCLIParser:
    """Test CLI argument parser."""

    def test_create_parser(self):
        """Test that the parser can be created."""
        from buildgen.cli import create_parser

        parser = create_parser()
        assert parser is not None
        assert parser.prog == "buildgen"

    def test_parser_new_command(self):
        """Test parsing 'new' command."""
        from buildgen.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["new", "myproject"])
        assert args.command == "new"
        assert args.name == "myproject"

    def test_parser_new_with_recipe(self):
        """Test parsing 'new' command with recipe."""
        from buildgen.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["new", "myproject", "-r", "cpp/executable"])
        assert args.command == "new"
        assert args.name == "myproject"
        assert args.recipe == "cpp/executable"

    def test_parser_list_command(self):
        """Test parsing 'list' command."""
        from buildgen.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["list"])
        assert args.command == "list"

    def test_parser_list_with_category(self):
        """Test parsing 'list' command with category filter."""
        from buildgen.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["list", "-c", "py"])
        assert args.command == "list"
        assert args.category == "py"
