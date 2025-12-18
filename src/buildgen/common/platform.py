"""Platform detection and Python system information."""

import os
import platform
import sys
import sysconfig

# Platform constant
PLATFORM = platform.system()


class PythonSystem:
    """Python system information for build configuration."""

    def __init__(self):
        self.name = "Python"
        self.version_info = sys.version_info

    def __str__(self):
        return self.version

    @property
    def version(self) -> str:
        """Semantic version of python: 3.11.10"""
        return f"{self.major}.{self.minor}.{self.patch}"

    @property
    def ver(self) -> str:
        """Short major.minor python version: 3.11"""
        return f"{self.major}.{self.minor}"

    @property
    def ver_nodot(self) -> str:
        """Concat major and minor version components: 311 in 3.11.7"""
        return self.ver.replace(".", "")

    @property
    def major(self) -> int:
        """Major component of semantic version: 3 in 3.11.7"""
        return self.version_info.major

    @property
    def minor(self) -> int:
        """Minor component of semantic version: 11 in 3.11.7"""
        return self.version_info.minor

    @property
    def patch(self) -> int:
        """Patch component of semantic version: 7 in 3.11.7"""
        return self.version_info.micro

    @property
    def name_version(self) -> str:
        """Return <name>-<fullversion>: e.g. Python-3.11.7"""
        return f"{self.name}-{self.version}"

    @property
    def name_ver(self) -> str:
        """Return <name.lower><ver>: e.g. python3.11"""
        return f"{self.name.lower()}{self.ver}"

    @property
    def executable_name(self) -> str:
        """Executable name."""
        name = self.name.lower()
        if PLATFORM == "Windows":
            name = f"{self.name}.exe"
        return name

    @property
    def libname(self) -> str:
        """Library name prefix."""
        return f"lib{self.name}"

    @property
    def linklib(self) -> str:
        """Name of library for linking."""
        return f"-l{self.name_ver}"

    @property
    def staticlib_name(self) -> str:
        """Static library name."""
        suffix = ".a"
        if PLATFORM == "Windows":
            suffix = ".lib"
        return f"{self.libname}{suffix}"

    @property
    def dylib_name(self) -> str:
        """Dynamic link library name."""
        if PLATFORM == "Windows":
            return f"{self.libname}.dll"
        if PLATFORM == "Darwin":
            return f"{self.libname}.dylib"
        return f"{self.libname}.so"

    @property
    def dylib_linkname(self) -> str:
        """Symlink to dylib."""
        if PLATFORM == "Darwin":
            return f"{self.libname}.dylib"
        return f"{self.libname}.so"

    @property
    def prefix(self) -> str:
        """Python system prefix."""
        return sysconfig.get_config_var("prefix")

    @property
    def include_dir(self) -> str:
        """Python include directory."""
        return sysconfig.get_config_var("INCLUDEPY")

    @property
    def config_h_dir(self) -> str:
        """Directory of config.h file."""
        return os.path.dirname(sysconfig.get_config_h_filename())

    @property
    def base_cflags(self) -> str:
        """Python base cflags."""
        return sysconfig.get_config_var("BASECFLAGS")

    @property
    def libs(self) -> str:
        """Python libs to link to."""
        return sysconfig.get_config_var("LIBS")

    @property
    def syslibs(self) -> str:
        """Python system libs to link to."""
        return sysconfig.get_config_var("SYSLIBS")

    @property
    def is_shared(self) -> bool:
        """Python system was built with enable_shared option."""
        return bool(sysconfig.get_config_var("Py_ENABLE_SHARED"))

    @property
    def libpl(self) -> str:
        """Directory of python dependencies."""
        return sysconfig.get_config_var("LIBPL")

    @property
    def extension_suffix(self) -> str:
        """Suffix of compiled python extension."""
        return sysconfig.get_config_var("EXT_SUFFIX")
