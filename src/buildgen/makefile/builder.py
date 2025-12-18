"""Direct compilation builder for Makefile-style builds."""

import os
from pathlib import Path
from typing import Optional

from buildgen.common.utils import UniqueList, PathLike, TestFunc, always_true
from buildgen.common.base import BaseBuilder


class Builder(BaseBuilder):
    """Configure and execute compiler instructions directly (without Makefile)."""

    def __init__(self, target: PathLike, strict: bool = False):
        super().__init__(target, strict)
        self._cc = "gcc"
        self._cxx = "g++"

    @property
    def cc(self) -> str:
        """C compiler."""
        return self._cc

    @cc.setter
    def cc(self, value: str) -> None:
        """Set C compiler."""
        self._cc = value

    @property
    def cxx(self) -> str:
        """C++ compiler."""
        return self._cxx

    @cxx.setter
    def cxx(self, value: str) -> None:
        """Set C++ compiler."""
        self._cxx = value

    @property
    def build_cmd(self) -> str:
        """Get the executable or extension build command."""
        return f"{self.CXX} {self.CXXFLAGS} {self.CPPFILES} {self.LDLIBS} {self.LDFLAGS} -o {self.TARGET}"

    @property
    def TARGET(self) -> str:
        """Compilation product."""
        return str(self.target)

    @property
    def CPPFILES(self) -> str:
        """C++ files as string."""
        return " ".join(self.cppfiles)

    @property
    def HPPFILES(self) -> str:
        """HPP files as string."""
        return " ".join(self.hppfiles)

    @property
    def CXX(self) -> str:
        """C++ compiler."""
        return self.cxx

    @property
    def CFLAGS(self) -> str:
        """C compiler flags as string."""
        return " ".join(self.cflags)

    @property
    def CXXFLAGS(self) -> str:
        """C++ compiler flags as string."""
        _flags = " ".join(self.cxxflags)
        return f"{_flags} {self.INCLUDEDIRS}"

    @property
    def INCLUDEDIRS(self) -> str:
        """Include directories as string."""
        return " ".join(self.include_dirs)

    @property
    def LINKDIRS(self) -> str:
        """Link directories as string."""
        return " ".join(self.link_dirs)

    @property
    def LDFLAGS(self) -> str:
        """Linker flags as string."""
        _flags = " ".join(self.ldflags)
        return f"{_flags} {self.LINKDIRS}"

    @property
    def LDLIBS(self) -> str:
        """Link libraries as string."""
        return " ".join(self.ldlibs)

    def _add_config_entries(
        self,
        attr: str,
        prefix: str = "",
        test_func: Optional[TestFunc] = None,
        *entries,
    ) -> None:
        """Add an entry to the configuration."""
        assert hasattr(self, attr), f"Invalid attribute: {attr}"
        _list = getattr(self, attr)
        if not test_func:
            test_func = always_true
        for entry in entries:
            assert test_func(entry), f"Invalid entry: {entry}"
            if entry in _list:
                if self.strict:
                    raise ValueError(f"entry: {entry} already exists in {attr} list")
                continue
            _list.append(f"{prefix}{entry}")

    def configure(self) -> None:
        """Configure the builder."""
        self._setup_defaults()

    def build(self, dry_run: bool = False) -> None:
        """Configure, then build executable or extension."""
        self.configure()
        if dry_run:
            print(self.build_cmd)
        else:
            print()
            self._execute(self.build_cmd)
            if self.cleanup_patterns or self.cleanup_targets:
                self.clean()

    def run_executable(self) -> None:
        """Run the executable."""
        print(f"Running {self.target}")
        self._execute(f"./{self.target}")

    def add_cppfiles(self, *entries: str) -> None:
        """Add C++ files to the configuration."""
        self._add_config_entries("_cppfiles", "", None, *entries)

    def add_hppfiles(self, *entries: str) -> None:
        """Add HPP files to the configuration."""
        self._add_config_entries("_hppfiles", "", None, *entries)

    def add_include_dirs(self, *entries):
        """Add include directories to the configuration."""
        self._add_config_entries("_include_dirs", "-I", os.path.isdir, *entries)

    def add_cflags(self, *entries):
        """Add compiler flags to the configuration."""
        self._add_config_entries("_cflags", "", None, *entries)

    def add_cxxflags(self, *entries):
        """Add C++ compiler flags to the configuration."""
        self._add_config_entries("_cxxflags", "", None, *entries)

    def add_link_dirs(self, *entries):
        """Add link directories to the configuration."""
        self._add_config_entries("_link_dirs", "-L", os.path.isdir, *entries)

    def add_ldlibs(self, *entries):
        """Add link libraries to the configuration."""
        self._add_config_entries("_ldlibs", "", None, *entries)

    def add_ldflags(self, *entries):
        """Add linker flags to the configuration."""
        self._add_config_entries("_ldflags", "", None, *entries)

    def add_cleanup_patterns(self, *entries):
        """Add cleanup patterns to the configuration."""
        self._add_config_entries("_cleanup_patterns", "", None, *entries)

    def add_cleanup_targets(self, *entries):
        """Add cleanup targets to the configuration."""
        self._add_config_entries("_cleanup_targets", "", None, *entries)

    def _setup_defaults(self):
        """Setup default model configuration."""
        self.add_include_dirs(os.getcwd())
