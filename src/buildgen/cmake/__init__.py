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
from buildgen.cmake.functions import (
    # Project
    cmake_minimum_required,
    cmake_project,
    # Targets
    cmake_add_executable,
    cmake_add_library,
    cmake_add_custom_target,
    cmake_add_custom_command,
    # Target properties
    cmake_target_link_libraries,
    cmake_target_include_directories,
    cmake_target_compile_definitions,
    cmake_target_compile_options,
    cmake_target_compile_features,
    cmake_target_sources,
    cmake_set_target_properties,
    # Dependencies
    cmake_find_package,
    cmake_find_library,
    cmake_find_path,
    cmake_pkg_check_modules,
    # FetchContent
    cmake_fetchcontent_declare,
    cmake_fetchcontent_makeavailable,
    # Control flow
    cmake_if,
    cmake_foreach,
    cmake_function,
    cmake_macro,
    # Files and directories
    cmake_include,
    cmake_add_subdirectory,
    cmake_file_glob,
    cmake_configure_file,
    # Install
    cmake_install_targets,
    cmake_install_files,
    cmake_install_directory,
    # Messages
    cmake_message,
    # Generator expressions
    cmake_genex_target_file,
    cmake_genex_target_property,
    cmake_genex_build_interface,
    cmake_genex_install_interface,
    cmake_genex_config,
    cmake_genex_platform,
    cmake_genex_compiler,
)

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
    # Functions - Project
    "cmake_minimum_required",
    "cmake_project",
    # Functions - Targets
    "cmake_add_executable",
    "cmake_add_library",
    "cmake_add_custom_target",
    "cmake_add_custom_command",
    # Functions - Target properties
    "cmake_target_link_libraries",
    "cmake_target_include_directories",
    "cmake_target_compile_definitions",
    "cmake_target_compile_options",
    "cmake_target_compile_features",
    "cmake_target_sources",
    "cmake_set_target_properties",
    # Functions - Dependencies
    "cmake_find_package",
    "cmake_find_library",
    "cmake_find_path",
    "cmake_pkg_check_modules",
    # Functions - FetchContent
    "cmake_fetchcontent_declare",
    "cmake_fetchcontent_makeavailable",
    # Functions - Control flow
    "cmake_if",
    "cmake_foreach",
    "cmake_function",
    "cmake_macro",
    # Functions - Files
    "cmake_include",
    "cmake_add_subdirectory",
    "cmake_file_glob",
    "cmake_configure_file",
    # Functions - Install
    "cmake_install_targets",
    "cmake_install_files",
    "cmake_install_directory",
    # Functions - Messages
    "cmake_message",
    # Functions - Generator expressions
    "cmake_genex_target_file",
    "cmake_genex_target_property",
    "cmake_genex_build_interface",
    "cmake_genex_install_interface",
    "cmake_genex_config",
    "cmake_genex_platform",
    "cmake_genex_compiler",
]
