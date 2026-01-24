<%page args="name, options={}" />
<%
raw_options = locals().get("options")
if not isinstance(raw_options, dict):
    raw_options = {}
opts = raw_options
test_framework = opts.get("test_framework", "catch2")
build_examples = bool(opts.get("build_examples", False))
build_cpp_tests = test_framework != "none"
%>

[project]
name = "${name}"
version = "0.1.0"
description = "Pybind11 extension with configurable native extras"
requires-python = ">=3.9"
readme = "README.md"
license = { text = "MIT" }
keywords = ["pybind11", "catch2", "gtest", "scikit-build"]
classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: C++",
    "Typing :: Typed",
]

[dependency-groups]
dev = [
    "mypy>=1.19.1",
    "pybind11-stubgen>=0.14",
    "pytest>=8.4.2",
    "pytest-cov>=7.0.0",
    "ruff>=0.14.9",
    "twine>=6.2.0",
]

[build-system]
requires = ["scikit-build-core", "pybind11", "pyproject-metadata"]
build-backend = "scikit_build_core.build"

[tool.scikit-build]
wheel.packages = ["src/${name}"]
cmake.args = []
cmake.build-type = "Release"
cmake.source-dir = "."
sdist.include = []
sdist.exclude = []
wheel.exclude = []

[tool.scikit-build.cmake.define]
BUILD_CPP_TESTS = ${"true" if build_cpp_tests else "false"}
TEST_FRAMEWORK = "${test_framework}"
BUILD_EMBEDDED_CLI = ${"true" if build_examples else "false"}
