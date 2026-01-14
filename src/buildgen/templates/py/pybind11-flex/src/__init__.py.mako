"""
${name} - Pybind11 bindings with optional native helpers.

Use the generated project.flex.json or CMake options to switch
between Catch2/GTest native harnesses and the embedded CLI sample.
"""

from ${name}._core import add, greet

__all__ = ["add", "greet"]
__version__ = "0.1.0"
