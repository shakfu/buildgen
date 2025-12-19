[build-system]
requires = ["scikit-build-core", "nanobind"]
build-backend = "scikit_build_core.build"

[project]
name = "${name}"
version = "0.1.0"
description = "A Python extension module built with nanobind"
requires-python = ">=3.9"

[tool.scikit-build]
wheel.packages = ["src/${name}"]
