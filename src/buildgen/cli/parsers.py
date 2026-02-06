"""CLI argument parser setup for buildgen."""

import argparse

from buildgen.recipes import RECIPES
from buildgen.cli.commands import (
    cmd_new,
    cmd_list,
    cmd_test,
    cmd_generate,
    cmd_render,
    cmd_templates_list,
    cmd_templates_copy,
    cmd_templates_show,
    cmd_config_init,
    cmd_config_show,
    cmd_config_path,
)


def add_new_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Add 'new' command parser."""
    recipe_choices = list(RECIPES.keys())

    parser = subparsers.add_parser(
        "new",
        help="Create a new project from a recipe",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  buildgen new myapp                          # Default recipe (cpp/executable)
  buildgen new myapp -r cpp/executable        # Explicit recipe
  buildgen new myext --recipe py/pybind11     # Python extension
  buildgen new myext -r py/cython --env venv  # Use venv instead of uv
  buildgen new mylib -r c/static -o /tmp/lib  # Custom output directory

Use 'buildgen list' to see available recipes.""",
    )
    parser.add_argument(
        "name",
        help="Project name",
    )
    parser.add_argument(
        "-r",
        "--recipe",
        choices=recipe_choices,
        help="Recipe to use (default: cpp/executable)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory (default: ./<name>)",
    )
    parser.add_argument(
        "-e",
        "--env",
        choices=["uv", "venv"],
        default=None,
        help="Environment tool for py/* recipes (default: uv)",
    )
    parser.set_defaults(func=cmd_new)


def add_list_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Add 'list' command parser."""
    parser = subparsers.add_parser(
        "list",
        help="List available recipes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  buildgen list                 # List all recipes
  buildgen list --category py   # List Python extension recipes
  buildgen list -c cpp          # List C++ recipes""",
    )
    parser.add_argument(
        "-c",
        "--category",
        choices=["cpp", "c", "py"],
        help="Filter by category",
    )
    parser.set_defaults(func=cmd_list)


def add_test_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Add 'test' command parser."""
    recipe_choices = list(RECIPES.keys())

    parser = subparsers.add_parser(
        "test",
        help="Test recipe generation and building",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  buildgen test                           # Test generation only
  buildgen test --build                   # Test generation and building
  buildgen test --all                     # Build and run tests
  buildgen test --category py --all       # Test Python recipes
  buildgen test --name py/cython --all    # Test specific recipe
  buildgen test --build --keep -o /tmp    # Keep output for inspection""",
    )
    parser.add_argument(
        "-n",
        "--name",
        choices=recipe_choices,
        help="Test only this recipe",
    )
    parser.add_argument(
        "-c",
        "--category",
        choices=["cpp", "c", "py"],
        help="Test only recipes in this category",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory (default: temp directory)",
    )
    parser.add_argument(
        "-b",
        "--build",
        action="store_true",
        help="Build generated projects",
    )
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="Run tests (requires --build)",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Build and test (shortcut for --build --test)",
    )
    parser.add_argument(
        "-k",
        "--keep",
        action="store_true",
        help="Keep output directory after testing",
    )
    parser.set_defaults(func=cmd_test)


def add_generate_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Add 'generate' command parser."""
    parser = subparsers.add_parser(
        "generate",
        help="Generate config or build files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a boilerplate config file
  buildgen generate --config project.json
  buildgen generate --config project.yaml

  # Generate build files from existing config
  buildgen generate --from project.json
  buildgen generate --from project.json --makefile
  buildgen generate --from project.yaml --cmake""",
    )
    parser.add_argument(
        "--config",
        metavar="FILE",
        help="Generate a boilerplate config file",
    )
    parser.add_argument(
        "--from",
        dest="from_config",
        metavar="FILE",
        help="Generate build files from existing config",
    )
    parser.add_argument(
        "--makefile",
        action="store_true",
        help="Generate Makefile only (with --from)",
    )
    parser.add_argument(
        "--cmake",
        action="store_true",
        help="Generate CMakeLists.txt only (with --from)",
    )
    parser.set_defaults(func=cmd_generate)


def add_render_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Add 'render' command parser for configurable recipes."""
    parser = subparsers.add_parser(
        "render",
        help="Render a configurable recipe config into project files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  buildgen render myext/project.flex.json
  buildgen render project.json -o out/myext
  buildgen render project.flex.json --env venv
        """,
    )
    parser.add_argument(
        "config",
        help="Config file generated by 'buildgen new <name> -r <configurable>'",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory (default: alongside config, named after project)",
    )
    parser.add_argument(
        "-e",
        "--env",
        choices=["uv", "venv"],
        help="Override environment tool from the config options",
    )
    parser.set_defaults(func=cmd_render)


def add_templates_subparsers(subparsers: argparse._SubParsersAction) -> None:
    """Add templates subcommand parsers."""
    from buildgen.skbuild.templates import SKBUILD_TYPES
    from buildgen.templates.resolver import get_builtin_template_recipes

    # Build choices: recipe paths + legacy names for backward compat
    recipe_choices = get_builtin_template_recipes()
    legacy_choices = list(SKBUILD_TYPES.keys())
    all_choices = recipe_choices + legacy_choices

    templates_parser = subparsers.add_parser(
        "templates",
        help="Manage project templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Template Override Hierarchy:
  Templates are resolved in this order (first match wins):
  1. $BUILDGEN_TEMPLATES/{recipe}/  (environment variable)
  2. .buildgen/templates/{recipe}/  (project-local)
  3. ~/.buildgen/templates/{recipe}/ (user-global)
  4. Built-in templates

Examples:
  # List available templates
  buildgen templates list

  # Copy pybind11 templates for local customization
  buildgen templates copy py/pybind11

  # Copy templates to global location
  buildgen templates copy py/pybind11 --global

  # Show where templates are resolved from
  buildgen templates show py/pybind11
        """,
    )

    templates_subparsers = templates_parser.add_subparsers(
        dest="templates_command", help="Template commands"
    )

    # templates list
    list_parser = templates_subparsers.add_parser(
        "list",
        help="List available template types",
    )
    list_parser.set_defaults(func=cmd_templates_list)

    # templates copy
    copy_parser = templates_subparsers.add_parser(
        "copy",
        help="Copy templates for customization",
    )
    copy_parser.add_argument(
        "recipe",
        choices=all_choices,
        help="Recipe template to copy (e.g., py/pybind11)",
    )
    copy_parser.add_argument(
        "--global",
        dest="to_global",
        action="store_true",
        help="Copy to ~/.buildgen/templates/ instead of .buildgen/templates/",
    )
    copy_parser.set_defaults(func=cmd_templates_copy)

    # templates show
    show_parser = templates_subparsers.add_parser(
        "show",
        help="Show template resolution details",
    )
    show_parser.add_argument(
        "recipe",
        choices=all_choices,
        help="Recipe template to show (e.g., py/pybind11)",
    )
    show_parser.add_argument(
        "-e",
        "--env",
        choices=["uv", "venv"],
        default="uv",
        help="Environment tool (default: uv)",
    )
    show_parser.set_defaults(func=cmd_templates_show)


def add_config_subparsers(subparsers: argparse._SubParsersAction) -> None:
    """Add config subcommand parsers."""
    config_parser = subparsers.add_parser(
        "config",
        help="Manage user configuration (~/.buildgen/config.toml)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  buildgen config init    # Create ~/.buildgen/config.toml
  buildgen config show    # Display current config
  buildgen config path    # Print config file path
        """,
    )

    config_subparsers = config_parser.add_subparsers(
        dest="config_command", help="Config commands"
    )

    # config init
    init_parser = config_subparsers.add_parser(
        "init",
        help="Create a default config file",
    )
    init_parser.set_defaults(func=cmd_config_init)

    # config show
    show_parser = config_subparsers.add_parser(
        "show",
        help="Display current resolved config",
    )
    show_parser.set_defaults(func=cmd_config_show)

    # config path
    path_parser = config_subparsers.add_parser(
        "path",
        help="Print the config file path",
    )
    path_parser.set_defaults(func=cmd_config_path)


def create_parser() -> argparse.ArgumentParser:
    """Create the main CLI argument parser."""
    from buildgen import __version__
    from buildgen.makefile.cli import add_makefile_subparsers
    from buildgen.cmake.cli import add_cmake_subparsers

    parser = argparse.ArgumentParser(
        prog="buildgen",
        description="Build system generator - Makefile, CMake, and more",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Common Commands:
  new <name>            Create a new project from a recipe
  list                  List available recipes
  test                  Test recipe generation and building
  generate              Generate config or build files
  render <config>       Render configurable recipe configs

Advanced Commands:
  makefile              Direct Makefile generation
  cmake                 Direct CMake generation
  templates             Manage project templates

Examples:
  buildgen new myapp
  buildgen new myext -r py/pybind11
  buildgen list --category py
  buildgen test --all
  buildgen generate --config project.json
  buildgen generate --from project.json
  buildgen render project.flex.json
        """,
    )

    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # New simplified commands (Tier 1)
    add_new_subparser(subparsers)
    add_list_subparser(subparsers)
    add_test_subparser(subparsers)
    add_generate_subparser(subparsers)
    add_render_subparser(subparsers)

    # Advanced commands (Tier 3)
    add_makefile_subparsers(subparsers)
    add_cmake_subparsers(subparsers)
    add_templates_subparsers(subparsers)
    add_config_subparsers(subparsers)

    return parser
