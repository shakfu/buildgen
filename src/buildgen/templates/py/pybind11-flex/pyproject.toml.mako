<%page args="name, defaults={}, user={}, options={}, dep_versions={}" />
<%!
from buildgen.common import versions as V
%>\
<%
raw_options = locals().get("options")
if not isinstance(raw_options, dict):
    raw_options = {}
opts = raw_options
test_framework = opts.get("test_framework", "catch2")
build_examples = bool(opts.get("build_examples", False))
build_cpp_tests = test_framework != "none"
_defaults = defaults if isinstance(defaults, dict) else {}
_license = _defaults.get("license", "MIT")
_python_version = _defaults.get("python_version", str(V.PYTHON["floor"]))
_dv = {**V.PYPI, **(dep_versions if isinstance(dep_versions, dict) else {})}
_py_min_minor = int(_python_version.split(".")[1])
_py_max_minor = max(int(V.PYTHON["max_classifier_minor"]), _py_min_minor)

_author_parts = []
if user and isinstance(user, dict):
    if user.get("name"):
        _author_parts.append(f'name = "{user["name"]}"')
    if user.get("email"):
        _author_parts.append(f'email = "{user["email"]}"')
%>

[project]
name = "${name}"
version = "0.1.0"
description = "Pybind11 extension with configurable native extras"
requires-python = ">=${_python_version}"
readme = "README.md"
license = { text = "${_license}" }
% if _author_parts:
authors = [
    { ${", ".join(_author_parts)} }
]
% endif
keywords = ["pybind11", "catch2", "gtest", "scikit-build"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Programming Language :: Python :: 3",
% for _minor in range(_py_min_minor, _py_max_minor + 1):
    "Programming Language :: Python :: 3.${_minor}",
% endfor
    "Programming Language :: C++",
    "Typing :: Typed",
]

[dependency-groups]
dev = [
% for _tool in sorted(V.DEV_TOOLS + ("pybind11-stubgen",)):
    "${V.requirement(_tool, _dv)}",
% endfor
]

[build-system]
requires = ["${V.requirement('scikit-build-core', _dv)}", "pybind11"]
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

[tool.mypy]
strict = true

[[tool.mypy.overrides]]
# The compiled extension ships no stubs. Everything else stays checked.
module = "${name}._core"
ignore_missing_imports = true
