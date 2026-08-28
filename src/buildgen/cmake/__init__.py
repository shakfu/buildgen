"""CMake generation and building support."""

from buildgen.cmake.builder import CMakeBuilder
from buildgen.cmake.functions import Cm
from buildgen.cmake.generator import CMakeListsGenerator, CMakeWriter
from buildgen.cmake.variables import (
    CMakeCacheVar,
    CMakeEnvVar,
    CMakeOption,
    CMakeVar,
    cmake_bool,
    cmake_cache_var,
    cmake_env_var,
    cmake_var,
)

# Grouped by category rather than sorted; the groups are the useful order.
__all__ = [  # noqa: RUF022
    # Variables
    "CMakeVar",
    "CMakeCacheVar",
    "CMakeOption",
    "CMakeEnvVar",
    "cmake_var",
    "cmake_env_var",
    "cmake_cache_var",
    "cmake_bool",
    # Generator
    "CMakeListsGenerator",
    "CMakeWriter",
    "CMakeBuilder",
    # Functions
    "Cm",
]
