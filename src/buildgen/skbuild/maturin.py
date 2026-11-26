"""Option resolution shared by the ``py/maturin`` and ``py/maturin-flex`` templates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

BINDINGS = ("pyo3", "cffi", "uniffi")


@dataclass(frozen=True)
class MaturinOptions:
    """Resolved build options for a maturin project."""

    bindings: str
    abi3: bool
    rust_tests: bool

    @property
    def generated_module(self) -> bool:
        """True when maturin writes the Python side of ``_core`` at build time."""
        return self.bindings != "pyo3"


def resolve(options: dict[str, Any] | None) -> MaturinOptions:
    """Resolve template options, applying defaults.

    Raises:
        ValueError: If an option has an invalid value.
    """
    opts = options if isinstance(options, dict) else {}
    bindings = opts.get("bindings", "pyo3")
    if bindings not in BINDINGS:
        raise ValueError(
            f"Invalid bindings: {bindings!r}. Valid: {', '.join(BINDINGS)}"
        )
    for key in ("abi3", "rust_tests"):
        if key in opts and not isinstance(opts[key], bool):
            raise ValueError(f"Option {key!r} must be true or false")
    # abi3 is a CPython ABI; cffi and uniffi wheels do not link it at all.
    abi3 = bool(opts.get("abi3", True)) and bindings == "pyo3"
    return MaturinOptions(bindings, abi3, bool(opts.get("rust_tests", False)))
