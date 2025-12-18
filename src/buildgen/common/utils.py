"""Common utility functions and classes."""

import subprocess
from typing import Any, Callable, Optional, TypeAlias

# Type aliases
PathLike: TypeAlias = "Path | str"
TestFunc: TypeAlias = Callable[[str], bool]


def always_true(_: Any) -> bool:
    """Dummy test function that always returns True."""
    return True


def env_var(name: str) -> str:
    """Return a shell environment variable reference."""
    return f"${{{name}}}"


def check_output(cmd: str) -> Optional[str]:
    """Run a command and return its output, or None if command not found."""
    try:
        return subprocess.check_output(cmd.split(), encoding="utf8").strip()
    except FileNotFoundError:
        return None


class UniqueList(list):
    """A list subclass that maintains unique elements while preserving order."""

    def __init__(self, iterable=None):
        """Initialize UniqueList, ensuring all elements are unique."""
        super().__init__()
        if iterable is not None:
            for item in iterable:
                self.add(item)

    def __repr__(self):
        """Custom representation showing it's a UniqueList."""
        return f"UniqueList({super().__repr__()})"

    def __iadd__(self, other):
        """Override += operator to maintain uniqueness."""
        self.extend(other)
        return self

    def __add__(self, other):
        """Override + operator to return a new UniqueList."""
        result = UniqueList(self)
        result.extend(other)
        return result

    def add(self, item):
        """Add an item only if it's not already in the list."""
        if item not in self:
            self.append(item)
        return self

    def append(self, item):
        """Override append to maintain uniqueness."""
        if item not in self:
            super().append(item)

    def extend(self, iterable):
        """Override extend to maintain uniqueness."""
        for item in iterable:
            self.add(item)

    def insert(self, index, item):
        """Override insert to maintain uniqueness."""
        if item not in self:
            super().insert(index, item)

    def first(self):
        """Get first item if it exists."""
        return self[0]

    def last(self):
        """Get last item if it exists."""
        return self[-1]
