<%page args="name, framework, framework_pkg, description, lang_classifier, options={}" />
<%
# Handle optional extra build requirements
extra_requires = f', "{framework_pkg}"' if framework_pkg else ''
%>
[project]
name = "${name}"
version = "0.1.0"
description = "${description}"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.10"
keywords = ["${framework}", "python", "extension"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Programming Language :: ${lang_classifier}",
    "Typing :: Typed",
]

[dependency-groups]
dev = [
    "mypy>=1.19.1",
    "pytest>=8.4.2",
    "pytest-cov>=7.0.0",
    "ruff>=0.14.9",
    "twine>=6.2.0",
]

[build-system]
requires = ["scikit-build-core>=0.8"${extra_requires}]
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
