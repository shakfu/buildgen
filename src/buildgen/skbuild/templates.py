"""Template strings for scikit-build-core project types."""

# =============================================================================
# pybind11 Templates
# =============================================================================

PYBIND11_PYPROJECT = """\
[build-system]
requires = ["scikit-build-core", "pybind11"]
build-backend = "scikit_build_core.build"

[project]
name = "{name}"
version = "0.1.0"
description = "A Python extension module built with pybind11"
requires-python = ">=3.9"

[tool.scikit-build]
wheel.packages = ["src/{name}"]
"""

PYBIND11_CMAKE = """\
cmake_minimum_required(VERSION 3.15...3.30)
project(${{SKBUILD_PROJECT_NAME}} VERSION ${{SKBUILD_PROJECT_VERSION}} LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(_core MODULE src/{name}/_core.cpp)

install(TARGETS _core DESTINATION {name})
"""

PYBIND11_CORE_CPP = """\
#include <pybind11/pybind11.h>
#include <string>

namespace py = pybind11;

int add(int a, int b) {{
    return a + b;
}}

std::string greet(const std::string& name) {{
    return "Hello, " + name + "!";
}}

PYBIND11_MODULE(_core, m) {{
    m.doc() = "{name} extension module";

    m.def("add", &add, "Add two integers",
          py::arg("a"), py::arg("b"));

    m.def("greet", &greet, "Return a greeting string",
          py::arg("name"));
}}
"""

PYBIND11_INIT_PY = '''\
"""
{name} - A Python extension module built with pybind11.

Example usage:
    >>> import {name}
    >>> {name}.add(1, 2)
    3
    >>> {name}.greet("World")
    'Hello, World!'
"""

from {name}._core import add, greet

__all__ = ["add", "greet"]
__version__ = "0.1.0"
'''

PYBIND11_TEST = '''\
"""Tests for {name} extension module."""

import {name}


def test_add():
    """Test add function."""
    assert {name}.add(1, 2) == 3
    assert {name}.add(-1, 1) == 0
    assert {name}.add(0, 0) == 0


def test_greet():
    """Test greet function."""
    assert {name}.greet("World") == "Hello, World!"
    assert {name}.greet("Python") == "Hello, Python!"
'''

# =============================================================================
# Cython Templates
# =============================================================================

CYTHON_PYPROJECT = """\
[build-system]
requires = ["scikit-build-core", "cython"]
build-backend = "scikit_build_core.build"

[project]
name = "{name}"
version = "0.1.0"
description = "A Python extension module built with Cython"
requires-python = ">=3.9"

[tool.scikit-build]
wheel.packages = ["src/{name}"]
"""

CYTHON_CMAKE = """\
cmake_minimum_required(VERSION 3.15...3.30)
project(${{SKBUILD_PROJECT_NAME}} VERSION ${{SKBUILD_PROJECT_VERSION}} LANGUAGES C)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(Cython REQUIRED)

cython_transpile(src/{name}/_core.pyx LANGUAGE C OUTPUT_VARIABLE _core_c)

python_add_library(_core MODULE ${{_core_c}} WITH_SOABI)

install(TARGETS _core DESTINATION {name})
"""

CYTHON_CORE_PYX = '''\
# cython: language_level=3
"""
{name} Cython extension module.

Provides fast implementations of add and greet functions.
"""


cpdef int add(int a, int b):
    """Add two integers.

    Args:
        a: First integer.
        b: Second integer.

    Returns:
        Sum of a and b.
    """
    return a + b


cpdef str greet(str name):
    """Return a greeting string.

    Args:
        name: Name to greet.

    Returns:
        Greeting string.
    """
    return f"Hello, {{name}}!"
'''

CYTHON_INIT_PY = '''\
"""
{name} - A Python extension module built with Cython.

Example usage:
    >>> import {name}
    >>> {name}.add(1, 2)
    3
    >>> {name}.greet("World")
    'Hello, World!'
"""

from {name}._core import add, greet

__all__ = ["add", "greet"]
__version__ = "0.1.0"
'''

CYTHON_TEST = '''\
"""Tests for {name} Cython extension module."""

import {name}


def test_add():
    """Test add function."""
    assert {name}.add(1, 2) == 3
    assert {name}.add(-1, 1) == 0
    assert {name}.add(0, 0) == 0


def test_greet():
    """Test greet function."""
    assert {name}.greet("World") == "Hello, World!"
    assert {name}.greet("Python") == "Hello, Python!"
'''

# =============================================================================
# C Extension Templates
# =============================================================================

C_PYPROJECT = """\
[build-system]
requires = ["scikit-build-core"]
build-backend = "scikit_build_core.build"

[project]
name = "{name}"
version = "0.1.0"
description = "A Python C extension module"
requires-python = ">=3.9"

[tool.scikit-build]
wheel.packages = ["src/{name}"]
"""

C_CMAKE = """\
cmake_minimum_required(VERSION 3.15...3.30)
project(${{SKBUILD_PROJECT_NAME}} VERSION ${{SKBUILD_PROJECT_VERSION}} LANGUAGES C)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)

python_add_library(_core MODULE src/{name}/_core.c WITH_SOABI)

install(TARGETS _core DESTINATION {name})
"""

C_CORE_C = """\
#define PY_SSIZE_T_CLEAN
#include <Python.h>

static PyObject* {name}_add(PyObject* self, PyObject* args) {{
    int a, b;
    if (!PyArg_ParseTuple(args, "ii", &a, &b)) {{
        return NULL;
    }}
    return PyLong_FromLong(a + b);
}}

static PyObject* {name}_greet(PyObject* self, PyObject* args) {{
    const char* name;
    if (!PyArg_ParseTuple(args, "s", &name)) {{
        return NULL;
    }}
    return PyUnicode_FromFormat("Hello, %s!", name);
}}

static PyMethodDef {name}_methods[] = {{
    {{"add", {name}_add, METH_VARARGS, "Add two integers."}},
    {{"greet", {name}_greet, METH_VARARGS, "Return a greeting string."}},
    {{NULL, NULL, 0, NULL}}
}};

static struct PyModuleDef {name}_module = {{
    PyModuleDef_HEAD_INIT,
    "_core",
    "{name} C extension module",
    -1,
    {name}_methods
}};

PyMODINIT_FUNC PyInit__core(void) {{
    return PyModule_Create(&{name}_module);
}}
"""

C_INIT_PY = '''\
"""
{name} - A Python C extension module.

Example usage:
    >>> import {name}
    >>> {name}.add(1, 2)
    3
    >>> {name}.greet("World")
    'Hello, World!'
"""

from {name}._core import add, greet

__all__ = ["add", "greet"]
__version__ = "0.1.0"
'''

C_TEST = '''\
"""Tests for {name} C extension module."""

import {name}


def test_add():
    """Test add function."""
    assert {name}.add(1, 2) == 3
    assert {name}.add(-1, 1) == 0
    assert {name}.add(0, 0) == 0


def test_greet():
    """Test greet function."""
    assert {name}.greet("World") == "Hello, World!"
    assert {name}.greet("Python") == "Hello, Python!"
'''

# =============================================================================
# nanobind Templates
# =============================================================================

NANOBIND_PYPROJECT = """\
[build-system]
requires = ["scikit-build-core", "nanobind"]
build-backend = "scikit_build_core.build"

[project]
name = "{name}"
version = "0.1.0"
description = "A Python extension module built with nanobind"
requires-python = ">=3.9"

[tool.scikit-build]
wheel.packages = ["src/{name}"]
"""

NANOBIND_CMAKE = """\
cmake_minimum_required(VERSION 3.15...3.30)
project(${{SKBUILD_PROJECT_NAME}} VERSION ${{SKBUILD_PROJECT_VERSION}} LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(nanobind CONFIG REQUIRED)

nanobind_add_module(_core src/{name}/_core.cpp)

install(TARGETS _core DESTINATION {name})
"""

NANOBIND_CORE_CPP = """\
#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <string>

namespace nb = nanobind;

int add(int a, int b) {{
    return a + b;
}}

std::string greet(const std::string& name) {{
    return "Hello, " + name + "!";
}}

NB_MODULE(_core, m) {{
    m.doc() = "{name} extension module";

    m.def("add", &add, "Add two integers",
          nb::arg("a"), nb::arg("b"));

    m.def("greet", &greet, "Return a greeting string",
          nb::arg("name"));
}}
"""

NANOBIND_INIT_PY = '''\
"""
{name} - A Python extension module built with nanobind.

Example usage:
    >>> import {name}
    >>> {name}.add(1, 2)
    3
    >>> {name}.greet("World")
    'Hello, World!'
"""

from {name}._core import add, greet

__all__ = ["add", "greet"]
__version__ = "0.1.0"
'''

NANOBIND_TEST = '''\
"""Tests for {name} nanobind extension module."""

import {name}


def test_add():
    """Test add function."""
    assert {name}.add(1, 2) == 3
    assert {name}.add(-1, 1) == 0
    assert {name}.add(0, 0) == 0


def test_greet():
    """Test greet function."""
    assert {name}.greet("World") == "Hello, World!"
    assert {name}.greet("Python") == "Hello, Python!"
'''

# =============================================================================
# Common Makefile Frontend (shared by all skbuild types)
# =============================================================================

SKBUILD_MAKEFILE = """\
# Makefile frontend for scikit-build-core project
# Generated by buildgen for: {name}
#
# This Makefile wraps common build commands for convenience.
# The actual build is handled by scikit-build-core via pyproject.toml

.PHONY: all sync build rebuild test clean distclean wheel sdist help

# Default target
all: build

# Sync environment (initial setup, installs dependencies + package)
sync:
\tuv sync

# Build/rebuild the extension after code changes
build:
\tuv sync --reinstall-package {name}

# Alias for build
rebuild: build

# Run tests
test:
\tuv run pytest tests/ -v

# Build wheel
wheel:
\tuv build --wheel

# Build source distribution
sdist:
\tuv build --sdist

# Clean build artifacts
clean:
\t@rm -rf build/
\t@rm -rf dist/
\t@rm -rf *.egg-info/
\t@rm -rf src/*.egg-info/
\t@rm -rf .pytest_cache/
\t@find . -name "*.so" -delete
\t@find . -name "*.pyd" -delete
\t@find . -name "__pycache__" -type d -exec rm -rf {{}} + 2>/dev/null || true

# Clean everything including CMake cache
distclean: clean
\t@rm -rf CMakeCache.txt CMakeFiles/

# Show help
help:
\t@echo "Available targets:"
\t@echo "  all       - Build/rebuild the extension (default)"
\t@echo "  sync      - Sync environment (initial setup)"
\t@echo "  build     - Rebuild extension after code changes"
\t@echo "  rebuild   - Alias for build"
\t@echo "  test      - Run tests"
\t@echo "  wheel     - Build wheel distribution"
\t@echo "  sdist     - Build source distribution"
\t@echo "  clean     - Remove build artifacts"
\t@echo "  distclean - Remove all generated files"
\t@echo "  help      - Show this help message"
"""

SKBUILD_MAKEFILE_VENV = """\
# Makefile frontend for scikit-build-core project
# Generated by buildgen for: {name}
#
# This Makefile wraps common build commands for convenience.
# The actual build is handled by scikit-build-core via pyproject.toml
#
# Assumes a virtualenv is active. Override commands with PYTHON and PIP.

.PHONY: all build install dev test clean distclean wheel sdist help

PYTHON ?= python
PIP ?= pip

# Default target
all: build

# Build the extension (in-place for development)
build:
\t$(PIP) install --no-build-isolation -ve .

# Install the package
install:
\t$(PIP) install --no-build-isolation -v .

# Development install (editable)
dev:
\t$(PIP) install --no-build-isolation -ve .

# Run tests
test: build
\t$(PYTHON) -m pytest tests/ -v

# Build wheel
wheel:
\t$(PYTHON) -m build --wheel --no-isolation

# Build source distribution
sdist:
\t$(PYTHON) -m build --sdist --no-isolation

# Clean build artifacts
clean:
\t@rm -rf build/
\t@rm -rf dist/
\t@rm -rf *.egg-info/
\t@rm -rf src/*.egg-info/
\t@rm -rf .pytest_cache/
\t@find . -name "*.so" -delete
\t@find . -name "*.pyd" -delete
\t@find . -name "__pycache__" -type d -exec rm -rf {{}} + 2>/dev/null || true

# Clean everything including CMake cache
distclean: clean
\t@rm -rf CMakeCache.txt CMakeFiles/

# Show help
help:
\t@echo "Available targets:"
\t@echo "  all       - Build the extension (default)"
\t@echo "  build     - Build and install in development mode"
\t@echo "  install   - Install the package"
\t@echo "  dev       - Development install (editable)"
\t@echo "  test      - Run tests"
\t@echo "  wheel     - Build wheel distribution"
\t@echo "  sdist     - Build source distribution"
\t@echo "  clean     - Remove build artifacts"
\t@echo "  distclean - Remove all generated files"
\t@echo "  help      - Show this help message"
"""

# Makefile templates by environment tool
MAKEFILE_BY_ENV = {
    "uv": SKBUILD_MAKEFILE,
    "venv": SKBUILD_MAKEFILE_VENV,
}

# =============================================================================
# Template Registry
# =============================================================================

TEMPLATES = {
    "skbuild-pybind11": {
        "Makefile": SKBUILD_MAKEFILE,
        "pyproject.toml": PYBIND11_PYPROJECT,
        "CMakeLists.txt": PYBIND11_CMAKE,
        "src/{name}/__init__.py": PYBIND11_INIT_PY,
        "src/{name}/_core.cpp": PYBIND11_CORE_CPP,
        "tests/test_{name}.py": PYBIND11_TEST,
    },
    "skbuild-cython": {
        "Makefile": SKBUILD_MAKEFILE,
        "pyproject.toml": CYTHON_PYPROJECT,
        "CMakeLists.txt": CYTHON_CMAKE,
        "src/{name}/__init__.py": CYTHON_INIT_PY,
        "src/{name}/_core.pyx": CYTHON_CORE_PYX,
        "tests/test_{name}.py": CYTHON_TEST,
    },
    "skbuild-c": {
        "Makefile": SKBUILD_MAKEFILE,
        "pyproject.toml": C_PYPROJECT,
        "CMakeLists.txt": C_CMAKE,
        "src/{name}/__init__.py": C_INIT_PY,
        "src/{name}/_core.c": C_CORE_C,
        "tests/test_{name}.py": C_TEST,
    },
    "skbuild-nanobind": {
        "Makefile": SKBUILD_MAKEFILE,
        "pyproject.toml": NANOBIND_PYPROJECT,
        "CMakeLists.txt": NANOBIND_CMAKE,
        "src/{name}/__init__.py": NANOBIND_INIT_PY,
        "src/{name}/_core.cpp": NANOBIND_CORE_CPP,
        "tests/test_{name}.py": NANOBIND_TEST,
    },
}

SKBUILD_TYPES = {
    "skbuild-pybind11": "Python extension using pybind11 (C++ bindings)",
    "skbuild-cython": "Python extension using Cython",
    "skbuild-c": "Python C extension (direct Python.h)",
    "skbuild-nanobind": "Python extension using nanobind (modern C++ bindings)",
}
