"""
${name} - A Python extension module built with nanobind.

Example usage:
    >>> import ${name}
    >>> ${name}.add(1, 2)
    3
    >>> ${name}.greet("World")
    'Hello, World!'
"""

from ${name}._core import add, greet

__all__ = ["add", "greet"]
__version__ = "0.1.0"
