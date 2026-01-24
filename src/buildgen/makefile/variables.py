"""Makefile variable classes for different assignment types."""

import subprocess
from typing import Optional

# Lazy-loaded make version for syntax compatibility
_VERSION: Optional[float] = None


def get_make_version() -> float:
    """Get GNU Make version, with lazy loading and graceful fallback.

    Returns:
        Make version as a float (e.g., 4.4). Defaults to 4.0 if make
        is not installed or version cannot be determined.
    """
    global _VERSION
    if _VERSION is None:
        try:
            output = subprocess.check_output(
                ["make", "-v"],
                stderr=subprocess.DEVNULL,
                encoding="utf-8",
            )
            version_str = output.split("\n")[0].replace("GNU Make ", "")
            # Parse major.minor from version string (e.g., "4.4.1" -> 4.4)
            parts = version_str.split(".")
            _VERSION = float(f"{parts[0]}.{parts[1]}")
        except (FileNotFoundError, subprocess.CalledProcessError, ValueError, IndexError):
            _VERSION = 4.0  # Default to modern Make syntax
    return _VERSION


class Var:
    """Recursively Expanded Variable (=)."""

    assign_op = "="

    def __init__(self, key: str, *values):
        self.key = key
        if not values:
            raise ValueError("must enter at least one value")
        self.value = values[0] if len(values) == 1 else "\n".join(values)

    def __str__(self):
        if "\n" in self.value:
            lines = self.value.split("\n")
            values = "\n".join(lines)
            if get_make_version() > 3.81:
                return f"define {self.key} {self.assign_op}\n{values}\nendef\n"
            else:
                return f"define {self.key}\n{values}\nendef\n"
        return f"{self.key} {self.assign_op} {self.value}"


class SVar(Var):
    """Simply Expanded Variable (:=)."""

    assign_op = ":="


class IVar(Var):
    """Immediately Expanded Variable (:::=)."""

    assign_op = ":::="


class CVar(Var):
    """Conditional Variable (?=)."""

    assign_op = "?="


class AVar(Var):
    """Appended Variable (+=)."""

    assign_op = "+="
