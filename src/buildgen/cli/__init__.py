"""CLI package for buildgen.

This module provides backward-compatible imports for the refactored CLI.
The CLI is now split into:
- commands.py: Command implementations
- parsers.py: Argument parser setup
- main.py: Entry point
"""

from buildgen.cli.commands import (
    cmd_config_init,
    cmd_config_path,
    cmd_config_show,
    cmd_doctor,
    cmd_generate,
    cmd_list,
    cmd_lock,
    cmd_new,
    cmd_render,
    cmd_templates_copy,
    cmd_templates_list,
    cmd_templates_show,
    cmd_test,
    cmd_validate,
)
from buildgen.cli.main import main
from buildgen.cli.parsers import create_parser

__all__ = [
    "cmd_config_init",
    "cmd_config_path",
    "cmd_config_show",
    "cmd_doctor",
    "cmd_generate",
    "cmd_list",
    "cmd_lock",
    "cmd_new",
    "cmd_render",
    "cmd_templates_copy",
    "cmd_templates_list",
    "cmd_templates_show",
    "cmd_test",
    "cmd_validate",
    "create_parser",
    "main",
]
