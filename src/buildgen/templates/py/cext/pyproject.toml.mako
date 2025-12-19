[build-system]
requires = ["scikit-build-core"]
build-backend = "scikit_build_core.build"

[project]
name = "${name}"
version = "0.1.0"
description = "A Python C extension module"
requires-python = ">=3.9"

[tool.scikit-build]
wheel.packages = ["src/${name}"]
