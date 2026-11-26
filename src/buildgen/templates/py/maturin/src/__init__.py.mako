<%!
from buildgen.skbuild.maturin import resolve
%>\
<%
_m = resolve(context.get("options"))
_label = {"pyo3": "PyO3", "cffi": "cffi", "uniffi": "UniFFI"}[_m.bindings]
%>\
"""
${name} - A Python extension module written in Rust with ${_label}.

Example usage:
    >>> import ${name}
    >>> ${name}.add(1, 2)
    3
    >>> ${name}.greet("World")
    'Hello, World!'
"""

% if _m.bindings == "cffi":
from ${name}._core import ffi, lib


def add(a: int, b: int) -> int:
    """Add two integers."""
    return int(lib.core_add(a, b))


def greet(name: str) -> str:
    """Return a greeting."""
    ptr = lib.core_greet(name.encode())
    if ptr == ffi.NULL:
        raise ValueError("name must not contain NUL characters")
    try:
        return bytes(ffi.string(ptr)).decode()
    finally:
        lib.core_free_string(ptr)


% else:
from ${name}._core import add, greet

% endif
__all__ = ["add", "greet"]
__version__ = "0.1.0"
