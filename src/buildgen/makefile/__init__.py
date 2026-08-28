"""Makefile generation and direct compilation support."""

from buildgen.makefile.builder import Builder
from buildgen.makefile.functions import (
    AUTOMATIC_VARIABLES,
    Mk,
    auto_var,
    get_auto_var_help,
)
from buildgen.makefile.generator import MakefileGenerator, MakefileWriter
from buildgen.makefile.variables import AVar, CVar, IVar, SVar, Var

# Grouped by category rather than sorted; the groups are the useful order.
__all__ = [  # noqa: RUF022
    # Variables
    "Var",
    "SVar",
    "IVar",
    "CVar",
    "AVar",
    # Generator
    "MakefileGenerator",
    "MakefileWriter",
    "Builder",
    # Functions
    "AUTOMATIC_VARIABLES",
    "auto_var",
    "get_auto_var_help",
    "Mk",
]
