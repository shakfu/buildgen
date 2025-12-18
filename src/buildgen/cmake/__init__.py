"""CMake generation and building support."""

from buildgen.cmake.variables import (
    CMakeVar,
    CMakeCacheVar,
    CMakeOption,
    CMakeEnvVar,
    cmake_var,
    cmake_env_var,
    cmake_cache_var,
    cmake_bool,
)
from buildgen.cmake.generator import CMakeListsGenerator, CMakeWriter
from buildgen.cmake.builder import CMakeBuilder
from buildgen.cmake.functions import Cm

__all__ = [
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
