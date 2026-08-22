<%page args="name, framework, framework_pkg, description, lang_classifier, defaults={}, user={}, options={}, dep_versions={}, native=True, keywords=None" />
<%
# Handle optional extra build requirements
extra_requires = f', "{framework_pkg}"' if framework_pkg else ''
_defaults = defaults if isinstance(defaults, dict) else {}
_license = _defaults.get("license", "MIT")
_python_version = _defaults.get("python_version", "3.10")
_dv = dep_versions if isinstance(dep_versions, dict) else {}
# Python version classifiers span the requires-python floor up to the latest known release
_py_min_minor = int(_python_version.split(".")[1])
_py_max_minor = max(14, _py_min_minor)
# native=False -> pure-Python distribution: no compiler, no CMake, hatchling backend.
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
    "mypy>=${_dv.get('mypy', '1.19.1')}",
    "pytest>=${_dv.get('pytest', '8.4.2')}",
    "pytest-cov>=${_dv.get('pytest-cov', '7.0.0')}",
    "ruff>=${_dv.get('ruff', '0.14.9')}",
    "twine>=${_dv.get('twine', '7.0.0')}",
]

% if native:
[build-system]
requires = ["scikit-build-core>=${_dv.get('scikit-build-core', '0.12')}"${extra_requires}]
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
% else:
[build-system]
requires = ["hatchling>=${_dv.get('hatchling', '1.27.0')}"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/${name}"]

[tool.hatch.build.targets.sdist]
include = ["src/${name}", "tests", "README.md", "LICENSE", "CHANGELOG.md"]
% endif
