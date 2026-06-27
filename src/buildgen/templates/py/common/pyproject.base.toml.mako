<%page args="name, framework, framework_pkg, description, lang_classifier, defaults={}, user={}, options={}, dep_versions={}" />
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
keywords = ["${framework}", "python", "extension"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Programming Language :: Python :: 3",
% for _minor in range(_py_min_minor, _py_max_minor + 1):
    "Programming Language :: Python :: 3.${_minor}",
% endfor
    "Programming Language :: ${lang_classifier}",
    "Typing :: Typed",
]

[dependency-groups]
dev = [
    "mypy>=${_dv.get('mypy', '1.19.1')}",
    "pytest>=${_dv.get('pytest', '8.4.2')}",
    "pytest-cov>=${_dv.get('pytest-cov', '7.0.0')}",
    "ruff>=${_dv.get('ruff', '0.14.9')}",
    "twine>=${_dv.get('twine', '6.2.0')}",
]

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
