<%page args="name, framework, framework_pkg, description, lang_classifier, defaults={}, user={}, options={}, dep_versions={}, native=True, keywords=None" />
<%!
from buildgen.common import versions as V
%>\
<%
# Handle optional extra build requirements
extra_requires = f', "{framework_pkg}"' if framework_pkg else ''
_defaults = defaults if isinstance(defaults, dict) else {}
_license = _defaults.get("license", "MIT")
_python_version = _defaults.get("python_version", str(V.PYTHON["floor"]))
# Resolved versions (PyPI lookup, user pins) layered over the central floors.
_dv = {**V.PYPI, **(dep_versions if isinstance(dep_versions, dict) else {})}
# Python version classifiers span the requires-python floor up to the latest known release
_py_min_minor = int(_python_version.split(".")[1])
_py_max_minor = max(int(V.PYTHON["max_classifier_minor"]), _py_min_minor)
# native=False -> pure-Python distribution: no compiler, no CMake, uv_build backend.
_keywords = keywords if keywords else ([framework, "python", "extension"] if native else ["python", "library"])
%>
[project]
name = "${name}"
version = "0.1.0"
description = "${description}"
readme = "README.md"
license = { text = "${_license}" }
<%
_author_parts = []
if user:
    if user.get("name"):
        _author_parts.append(f'name = "{user["name"]}"')
    if user.get("email"):
        _author_parts.append(f'email = "{user["email"]}"')
%>\
% if _author_parts:
authors = [
    { ${", ".join(_author_parts)} }
]
% endif
requires-python = ">=${_python_version}"
keywords = [${", ".join('"%s"' % k for k in _keywords)}]
% if not native:
# This project intentionally has no runtime dependencies.
dependencies = []
% endif
classifiers = [
    "Development Status :: 3 - Alpha",
    "Programming Language :: Python :: 3",
% for _minor in range(_py_min_minor, _py_max_minor + 1):
    "Programming Language :: Python :: 3.${_minor}",
% endfor
% if lang_classifier:
    "Programming Language :: ${lang_classifier}",
% endif
% if not native:
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
% endif
    "Typing :: Typed",
]

[dependency-groups]
dev = [
% for _tool in V.DEV_TOOLS:
    "${V.requirement(_tool, _dv)}",
% endfor
]

% if native:
[build-system]
requires = ["${V.requirement('scikit-build-core', _dv)}"${extra_requires}]
build-backend = "scikit_build_core.build"

[tool.scikit-build]
wheel.packages = ["src/${name}"]
cmake.args = []
cmake.define = {}
cmake.build-type = "Release"
cmake.source-dir = "."
sdist.include = []
sdist.exclude = []
wheel.exclude = []

[tool.mypy]
strict = true

[[tool.mypy.overrides]]
# The compiled extension ships no stubs. Everything else stays checked.
module = "${name}._core"
ignore_missing_imports = true
% else:
[build-system]
requires = ["${V.requirement('uv-build', _dv)}"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-name = "${name}"
module-root = "src"
source-include = ["tests/**", "CHANGELOG.md", "LICENSE"]
% endif
