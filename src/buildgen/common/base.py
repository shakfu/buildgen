"""Abstract base classes for build system generators and builders."""

import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from buildgen.common.utils import UniqueList, PathLike


class BaseGenerator(ABC):
    """Abstract base class for build file generators (Makefile, CMakeLists.txt, etc.)."""

    def __init__(self, path: PathLike, strict: bool = False):
        """Initialize the generator.

        Args:
            path: Output path for the generated build file.
            strict: If True, raise errors on duplicate entries.
        """
        self.path = path
        self.strict = strict
        self.vars: dict[str, object] = {}
        self.var_order: UniqueList = UniqueList()
        self.include_dirs: UniqueList = UniqueList()
        self.cflags: UniqueList = UniqueList()
        self.cxxflags: UniqueList = UniqueList()
        self.link_dirs: UniqueList = UniqueList()
        self.ldlibs: UniqueList = UniqueList()
        self.ldflags: UniqueList = UniqueList()
        self.targets: UniqueList = UniqueList()

    @abstractmethod
    def add_variable(self, key: str, value: str, var_type=None) -> None:
        """Add a variable to the build file."""
        pass

    @abstractmethod
    def add_target(
        self, name: str, recipe: Optional[str] = None, deps: Optional[list[str]] = None
    ) -> None:
        """Add a build target."""
        pass

    @abstractmethod
    def generate(self) -> None:
        """Generate the build file."""
        pass

    def add_include_dirs(self, *entries, **kwargs) -> None:
        """Add include directories."""
        pass

    def add_cflags(self, *entries, **kwargs) -> None:
        """Add C compiler flags."""
        pass

    def add_cxxflags(self, *entries, **kwargs) -> None:
        """Add C++ compiler flags."""
        pass

    def add_link_dirs(self, *entries, **kwargs) -> None:
        """Add link directories."""
        pass

    def add_ldlibs(self, *entries, **kwargs) -> None:
        """Add link libraries."""
        pass

    def add_ldflags(self, *entries, **kwargs) -> None:
        """Add linker flags."""
        pass


class BaseBuilder(ABC):
    """Abstract base class for direct compilation builders."""

    def __init__(self, target: PathLike, strict: bool = False):
        """Initialize the builder.

        Args:
            target: Output target name/path.
            strict: If True, raise errors on duplicate entries.
        """
        self.target = target
        self.strict = strict
        self._cppfiles: UniqueList = UniqueList()
        self._hppfiles: UniqueList = UniqueList()
        self._include_dirs: UniqueList = UniqueList()
        self._cflags: UniqueList = UniqueList()
        self._cxxflags: UniqueList = UniqueList()
        self._link_dirs: UniqueList = UniqueList()
        self._ldlibs: UniqueList = UniqueList()
        self._ldflags: UniqueList = UniqueList()
        self._cleanup_patterns: UniqueList = UniqueList()
        self._cleanup_targets: UniqueList = UniqueList()

    @abstractmethod
    def configure(self) -> None:
        """Configure the builder before building."""
        pass

    @abstractmethod
    def build(self, dry_run: bool = False) -> None:
        """Build the target."""
        pass

    def clean(self) -> None:
        """Clean up build artifacts."""
        for pattern in self._cleanup_patterns:
            for path in Path(".").glob(pattern):
                self._remove(path)
        for target in self._cleanup_targets:
            self._remove(target)

    def _execute(self, cmd: str) -> None:
        """Execute a shell command."""
        print(cmd)
        os.system(cmd)

    def _remove(self, path: PathLike) -> None:
        """Remove a file or directory."""
        path = Path(path)
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=False)
        else:
            try:
                path.unlink()
            except FileNotFoundError:
                pass

    # Property accessors for configuration lists
    @property
    def cppfiles(self) -> UniqueList:
        return self._cppfiles

    @cppfiles.setter
    def cppfiles(self, value: list[str]) -> None:
        self._cppfiles = UniqueList(value)

    @property
    def hppfiles(self) -> UniqueList:
        return self._hppfiles

    @hppfiles.setter
    def hppfiles(self, value: list[str]) -> None:
        self._hppfiles = UniqueList(value)

    @property
    def include_dirs(self) -> UniqueList:
        return self._include_dirs

    @include_dirs.setter
    def include_dirs(self, value: list[str]) -> None:
        self._include_dirs = UniqueList(value)

    @property
    def cflags(self) -> UniqueList:
        return self._cflags

    @cflags.setter
    def cflags(self, value: list[str]) -> None:
        self._cflags = UniqueList(value)

    @property
    def cxxflags(self) -> UniqueList:
        return self._cxxflags

    @cxxflags.setter
    def cxxflags(self, value: list[str]) -> None:
        self._cxxflags = UniqueList(value)

    @property
    def link_dirs(self) -> UniqueList:
        return self._link_dirs

    @link_dirs.setter
    def link_dirs(self, value: list[str]) -> None:
        self._link_dirs = UniqueList(value)

    @property
    def ldlibs(self) -> UniqueList:
        return self._ldlibs

    @ldlibs.setter
    def ldlibs(self, value: list[str]) -> None:
        self._ldlibs = UniqueList(value)

    @property
    def ldflags(self) -> UniqueList:
        return self._ldflags

    @ldflags.setter
    def ldflags(self, value: list[str]) -> None:
        self._ldflags = UniqueList(value)

    @property
    def cleanup_patterns(self) -> UniqueList:
        return self._cleanup_patterns

    @cleanup_patterns.setter
    def cleanup_patterns(self, value: list[str]) -> None:
        self._cleanup_patterns = UniqueList(value)

    @property
    def cleanup_targets(self) -> UniqueList:
        return self._cleanup_targets

    @cleanup_targets.setter
    def cleanup_targets(self, value: list[str]) -> None:
        self._cleanup_targets = UniqueList(value)
