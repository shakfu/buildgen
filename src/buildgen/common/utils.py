"""Common utility functions and classes."""

import subprocess
from pathlib import Path
from typing import Any, Callable, Generic, Iterable, Optional, TypeAlias, TypeVar

# Type aliases
PathLike: TypeAlias = Path | str
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


_T = TypeVar("_T")


class UniqueList(list[_T], Generic[_T]):
    """A list subclass that maintains unique elements while preserving order."""

    def __init__(self, iterable: Optional[Iterable[_T]] = None) -> None:
        """Initialize UniqueList, ensuring all elements are unique."""
        super().__init__()
        if iterable is not None:
            for item in iterable:
                self.add(item)

    def __repr__(self) -> str:
        """Custom representation showing it's a UniqueList."""
        return f"UniqueList({super().__repr__()})"

    def __iadd__(self, other: Iterable[_T]) -> "UniqueList[_T]":  # type: ignore[override]
        """Override += operator to maintain uniqueness."""
        self.extend(other)
        return self

    def __add__(self, other: Iterable[_T]) -> "UniqueList[_T]":  # type: ignore[override]
        """Override + operator to return a new UniqueList."""
        result: UniqueList[_T] = UniqueList(self)
        result.extend(other)
        return result

    def add(self, item: _T) -> "UniqueList[_T]":
        """Add an item only if it's not already in the list."""
        if item not in self:
            self.append(item)
        return self

    def append(self, item: _T) -> None:  # type: ignore[override]
        """Override append to maintain uniqueness."""
        if item not in self:
            super().append(item)

    def extend(self, iterable: Iterable[_T]) -> None:  # type: ignore[override]
        """Override extend to maintain uniqueness."""
        for item in iterable:
            self.add(item)

    def insert(self, index: int, item: _T) -> None:  # type: ignore[override]
        """Override insert to maintain uniqueness."""
        if item not in self:
            super().insert(index, item)

    def first(self) -> _T:
        """Get first item if it exists."""
        return self[0]

    def last(self) -> _T:
        """Get last item if it exists."""
        return self[-1]
