"""Makefile generation and direct compilation support."""

from buildgen.makefile.variables import Var, SVar, IVar, CVar, AVar
from buildgen.makefile.generator import MakefileGenerator, MakefileWriter
from buildgen.makefile.builder import Builder
from buildgen.makefile.functions import (
    AUTOMATIC_VARIABLES,
    auto_var,
    get_auto_var_help,
    Mk,
)

__all__ = [
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
