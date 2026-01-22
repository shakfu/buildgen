"""Makefile variable classes for different assignment types."""

import subprocess

# Get Make version for syntax compatibility
_version_str = (
    subprocess.check_output(["make", "-v"])
    .decode()
    .split("\n")[0]
    .replace("GNU Make ", "")
)
# Parse major.minor from version string (e.g., "4.4.1" -> 4.4)
_version_parts = _version_str.split(".")
VERSION = float(f"{_version_parts[0]}.{_version_parts[1]}")


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
            if VERSION > 3.81:
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
