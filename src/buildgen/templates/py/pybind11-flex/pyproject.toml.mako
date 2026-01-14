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

[build-system]
requires = ["scikit-build-core", "pybind11", "pyproject-metadata"]
build-backend = "scikit_build_core.build"

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

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pybind11-stubgen>=0.14",
]

[tool.scikit-build]
wheel.packages = ["src/${name}"]

[tool.scikit-build.cmake.define]
BUILD_CPP_TESTS = ${"true" if build_cpp_tests else "false"}
TEST_FRAMEWORK = "${test_framework}"
BUILD_EMBEDDED_CLI = ${"true" if build_examples else "false"}
