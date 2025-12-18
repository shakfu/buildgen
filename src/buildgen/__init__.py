"""buildgen: Build system generator package.

Supports generating Makefiles, CMakeLists.txt, and direct compilation.
"""

__version__ = "0.2.0"

# Re-export common utilities
from buildgen.common.utils import UniqueList, check_output, env_var
from buildgen.common.platform import PLATFORM, PythonSystem
from buildgen.common.project import ProjectConfig, TargetConfig, DependencyConfig

# Re-export Makefile components
from buildgen.makefile.variables import Var, SVar, IVar, CVar, AVar
from buildgen.makefile.generator import MakefileGenerator, MakefileWriter
from buildgen.makefile.builder import Builder as MakefileBuilder
from buildgen.makefile.functions import (
    AUTOMATIC_VARIABLES,
    auto_var,
    get_auto_var_help,
    makefile_wildcard,
    makefile_patsubst,
    makefile_subst,
    makefile_filter,
    makefile_filter_out,
    makefile_sort,
    makefile_word,
    makefile_words,
    makefile_wordlist,
    makefile_firstword,
    makefile_lastword,
    makefile_dir,
    makefile_notdir,
    makefile_suffix,
    makefile_basename,
    makefile_addsuffix,
    makefile_addprefix,
    makefile_join,
    makefile_realpath,
    makefile_abspath,
    makefile_if,
    makefile_or,
    makefile_and,
    makefile_foreach,
    makefile_call,
    makefile_eval,
    makefile_origin,
    makefile_flavor,
    makefile_value,
    makefile_shell,
    makefile_strip,
    makefile_findstring,
)

# Re-export CMake components
from buildgen.cmake.variables import (
    CMakeVar,
    CMakeCacheVar,
    CMakeOption,
    cmake_var,
    cmake_bool,
)
from buildgen.cmake.generator import CMakeListsGenerator
from buildgen.cmake.builder import CMakeBuilder

# Alias for backward compatibility
Builder = MakefileBuilder

__all__ = [
    # Version
    "__version__",
    # Common
    "UniqueList",
    "check_output",
    "env_var",
    "PLATFORM",
    "PythonSystem",
    # Project configuration
    "ProjectConfig",
    "TargetConfig",
    "DependencyConfig",
    # Makefile variables
    "Var",
    "SVar",
    "IVar",
    "CVar",
    "AVar",
    # Makefile generator
    "MakefileGenerator",
    "MakefileWriter",
    "Builder",
    # Makefile functions
    "AUTOMATIC_VARIABLES",
    "auto_var",
    "get_auto_var_help",
    "makefile_wildcard",
    "makefile_patsubst",
    "makefile_subst",
    "makefile_filter",
    "makefile_filter_out",
    "makefile_sort",
    "makefile_word",
    "makefile_words",
    "makefile_wordlist",
    "makefile_firstword",
    "makefile_lastword",
    "makefile_dir",
    "makefile_notdir",
    "makefile_suffix",
    "makefile_basename",
    "makefile_addsuffix",
    "makefile_addprefix",
    "makefile_join",
    "makefile_realpath",
    "makefile_abspath",
    "makefile_if",
    "makefile_or",
    "makefile_and",
    "makefile_foreach",
    "makefile_call",
    "makefile_eval",
    "makefile_origin",
    "makefile_flavor",
    "makefile_value",
    "makefile_shell",
    "makefile_strip",
    "makefile_findstring",
    # CMake
    "CMakeVar",
    "CMakeCacheVar",
    "CMakeOption",
    "cmake_var",
    "cmake_bool",
    "CMakeListsGenerator",
    "CMakeBuilder",
]
