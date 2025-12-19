# Changelog

All notable changes to this project will be documented in this file.

## [unreleased]

## [0.1.4]

### Added

- **Recipe-Based Project System** - New hierarchical naming convention for project types
  - Recipes use `category/variant` format: `cpp/executable`, `c/static`, `py/pybind11`
  - `--recipe` / `-r` CLI option: `buildgen project init -n myapp --recipe cpp/executable`
  - `buildgen project recipes` command to list all available recipes by category
  - Language is now encoded in recipe name (no need for separate `--lang` flag)

- **Recipe Registry** (`src/buildgen/recipes.py`)
  - `Recipe` dataclass with name, description, category, variant, build_system, language, framework
  - 21 built-in recipes: 7 C++, 7 C, 4 Python extension
  - Helper functions: `get_recipe()`, `get_recipes_by_category()`, `is_valid_recipe()`

- **C++ Template Files** (`templates/cpp/`)
  - `cpp/executable` - C++17 executable with CMakeLists.txt and src/main.cpp
  - `cpp/static` - Static library with source and headers
  - `cpp/shared` - Shared library (-fPIC) with source and headers
  - `cpp/header-only` - Interface library (header-only)
  - `cpp/library-with-tests` - Static library with test executable
  - `cpp/app-with-lib` - Executable with internal library
  - `cpp/full` - Complete project: library + app + tests

- **C Template Files** (`templates/c/`)
  - `c/executable` - C11 executable with CMakeLists.txt and src/main.c
  - `c/static` - Static library with source and headers
  - `c/shared` - Shared library (-fPIC) with source and headers
  - `c/header-only` - Interface library (header-only)
  - `c/library-with-tests` - Static library with test executable
  - `c/app-with-lib` - Executable with internal library
  - `c/full` - Complete project: library + app + tests

- **CMake Project Generator** (`src/buildgen/cmake/project_generator.py`)
  - Template-based generation for all C++ and C recipes
  - `CMakeProjectGenerator` class with template override support
  - Generates: CMakeLists.txt, Makefile, source files, headers, test files

- **CMake Makefile Frontend** (`templates/common/Makefile.cmake.mako`)
  - Convenience wrapper for cmake commands
  - Targets: build, configure, clean, rebuild, install, test
  - Variables: BUILD_DIR, BUILD_TYPE, CMAKE_FLAGS

### Changed

- **Template Directory Restructure** - Templates now use recipe-based paths
  - `templates/skbuild-pybind11/` -> `templates/py/pybind11/`
  - `templates/skbuild-cython/` -> `templates/py/cython/`
  - `templates/skbuild-c/` -> `templates/py/cext/`
  - `templates/skbuild-nanobind/` -> `templates/py/nanobind/`
- Template CLI commands updated to use recipe paths: `buildgen templates copy py/pybind11`
- Removed `--lang` flag from `project init` (language now determined by recipe)
- `project types` command now redirects to `project recipes`

## [0.1.3]

### Added

- **Template Override System** - Customize templates without modifying buildgen
  - Four-tier resolution: `$BUILDGEN_TEMPLATES` > `.buildgen/templates/` > `~/.buildgen/templates/` > built-in
  - Per-file override granularity (override just pyproject.toml, keep other defaults)
  - `TemplateResolver` class for programmatic template resolution

- **Template CLI Commands** (`buildgen templates`)
  - `buildgen templates list` - List available templates and show override status
  - `buildgen templates copy <type>` - Copy templates to `.buildgen/templates/` for customization
  - `buildgen templates copy <type> --global` - Copy to `~/.buildgen/templates/` for user defaults
  - `buildgen templates show <type>` - Show template file resolution details

- **Embedded Mako Template Engine** (Mako-Lite)
  - Integrated Mako template library for `${variable}` syntax
  - Removed external markupsafe dependency (inlined html_escape)
  - Reduced from ~16k to ~7k lines by removing unused modules

### Changed

- Templates are now `.mako` files in `src/buildgen/templates/` instead of Python strings
- Simplified template directory structure (removed redundant category nesting)
- Template paths: `templates/skbuild-pybind11/` instead of `templates/skbuild/skbuild-pybind11/`

## [0.1.2]

### Added

- **scikit-build-core Project Templates** (`buildgen project init -t <type>`)
  - `skbuild-pybind11` - Python extension using pybind11 (C++ bindings)
  - `skbuild-cython` - Python extension using Cython
  - `skbuild-c` - Python C extension (direct Python.h)
  - `skbuild-nanobind` - Python extension using nanobind (modern C++ bindings)
  - Each template includes: pyproject.toml, CMakeLists.txt, source files, __init__.py, tests

- **Makefile Frontend for skbuild Projects**
  - `make sync` - Initial environment setup (`uv sync`)
  - `make build` - Rebuild extension (`uv sync --reinstall-package <name>`)
  - `make test` - Run tests (`uv run pytest`)
  - `make wheel` / `make sdist` - Build distributions (`uv build`)
  - `make clean` / `make distclean` - Clean build artifacts

- **Environment Tool Option** (`--env`)
  - `--env uv` (default) - Use uv commands in generated Makefile
  - `--env venv` - Use pip/python commands for traditional virtualenv workflows
  - Example: `buildgen project init -t skbuild-pybind11 -n myext --env venv`

## [0.1.1]

### Added

- **CMake Generator**: Full CMakeLists.txt generation support
  - `CMakeListsGenerator` class for programmatic generation
  - Support for executables, static/shared/interface libraries
  - `find_package()` for system dependencies
  - `FetchContent` for git/URL dependencies
  - Install rules generation
  - C++ standard configuration

- **CMake Builder**: Wrapper for cmake commands
  - `CMakeBuilder.configure()` - cmake -S -B
  - `CMakeBuilder.build()` - cmake --build
  - `CMakeBuilder.install()` - cmake --install

- **Cross-Generator Project Configuration**
  - `ProjectConfig` dataclass for defining projects once
  - JSON and YAML configuration file support
  - `generate_makefile()` - generate Makefile from config
  - `generate_cmake()` - generate CMakeLists.txt from config
  - `generate_all()` - generate both build systems
  - `generate_cmake_with_frontend()` - CMake with Makefile wrapper

- **CMake Frontend Mode**
  - Generate CMakeLists.txt as the build system
  - Generate Makefile as a convenience wrapper
  - Targets: all, build, configure, clean, rebuild, install, test, help
  - Configurable BUILD_DIR, BUILD_TYPE, CMAKE_FLAGS

- **Project Templates** (`buildgen project init -t <type>`)
  - `executable` - Single executable
  - `static` - Static library
  - `shared` - Shared library
  - `header-only` - Header-only/interface library
  - `library-with-tests` - Library with test executable
  - `app-with-lib` - Executable with internal library
  - `full` - Library + app + tests with dependencies

- **CLI Commands**
  - `buildgen cmake generate` - Generate CMakeLists.txt
  - `buildgen cmake build` - Configure and build with cmake
  - `buildgen cmake clean` - Clean build directory
  - `buildgen project init` - Create project config from template
  - `buildgen project generate` - Generate from config file
  - `buildgen project types` - List available templates

- **Enhanced Makefile** for development workflow
  - `make lint` - Run ruff check
  - `make format` / `make format-check` - Code formatting with ruff
  - `make typecheck` - Run ty and mypy type checkers
  - `make build` - Build distribution with uv
  - `make check` - Build and verify with twine
  - `make publish` - Publish to PyPI

### Changed

- Refactored Makefile functions to `Mk` namespace class
  - `makefile_wildcard(...)` -> `Mk.wildcard(...)`
  - `makefile_patsubst(...)` -> `Mk.patsubst(...)`
  - All 30+ functions now accessed via `Mk.*`
  - Import: `from buildgen.makefile.functions import Mk`

- Refactored CMake functions to `Cm` namespace class
  - `cmake_minimum_required(...)` -> `Cm.minimum_required(...)`
  - `cmake_project(...)` -> `Cm.project(...)`
  - All 40+ functions now accessed via `Cm.*`
  - Import: `from buildgen.cmake.functions import Cm`

- Removed backward compatibility aliases for old function names

- Minimized package `__init__.py` exports for API flexibility

- Package restructured from single file to multi-module
- `MakefileGenerator` now inherits from `BaseGenerator`
- Unified CLI entry point (`buildgen`)

### Fixed

- Type checking errors for both `ty` and `mypy`
- Ruff lint errors and code formatting
- `UniqueList` generic type annotations

## [0.1.0] - Initial Release

### Added

- **Makefile Generator**: Programmatic Makefile generation
  - Variable types: `Var`, `SVar`, `IVar`, `CVar`, `AVar`
  - Pattern rules, phony targets, clean targets
  - Conditional blocks (ifeq, ifdef, ifndef)
  - Include directives

- **Direct Builder**: Compile without generating Makefile
  - `Builder` class for direct compilation

- **Makefile Functions**: Python helpers for Makefile functions
  - `Mk.wildcard()`, `Mk.patsubst()`, `Mk.subst()`
  - `Mk.if_()`, `Mk.foreach()`, `Mk.shell()`
  - And 20+ more via `Mk.*` namespace

- **Utilities**
  - `UniqueList` - Ordered set-like list
  - `PythonSystem` - Python installation info
  - `PLATFORM` - Platform detection
