# Changelog

All notable changes to this project will be documented in this file.

## [0.1.10]

### Added

- **User Configuration** (`~/.buildgen/config.toml`) - Global user-level configuration loaded via stdlib `tomllib`.
  - `[user]` section: `name` and `email` fields for author identity
  - `[defaults]` section: `license`, `cxx_standard`, `c_standard`, `python_version`, `env_tool`
  - `UserConfig` dataclass and `load_user_config()` in `buildgen.common.config`
  - User info flows into templates: LICENSE copyright, pyproject.toml `authors` field
  - Defaults flow into templates: C/C++ standard in CMakeLists.txt, license and requires-python in pyproject.toml

- **`buildgen config` subcommand**:
  - `buildgen config init` - Creates `~/.buildgen/config.toml` with commented template (refuses to overwrite)
  - `buildgen config show` - Displays current resolved config
  - `buildgen config path` - Prints the config file path

- **Comprehensive config tests** (`tests/test_config.py`) - 39 tests covering config loading, template integration, CLI commands, defaults wiring, license body rendering, and backward compatibility.

### Fixed

- **LICENSE body matches `defaults.license`** - The generated LICENSE file now renders the correct license text for MIT, BSD-2-Clause, BSD-3-Clause, ISC, and Apache-2.0. Previously, the LICENSE file always contained MIT text regardless of the configured license. Unsupported SPDX identifiers get a stub with a link to the full text.

- **`--env` flag sentinel bug** - Changed argparse default for `--env` from `"uv"` to `None` so that `defaults.env_tool` from user config is only applied when the user doesn't explicitly pass `--env`. Previously, `--env uv` (explicit) was indistinguishable from the argparse default, causing user config to incorrectly override an explicit CLI choice.

- **`_generate_config_file` missing context** - Configurable recipe templates (e.g., `py/pybind11-flex`) now receive user config context, enabling them to pre-fill author info and apply defaults.

- **pybind11-flex `python_version` fallback inconsistency** - Changed fallback from `"3.9"` to `"3.10"` to match the base pyproject template and documentation.

- **`_generate_config_file` type annotation** - Changed `user_config` parameter type from `Optional[Any]` to `Optional["UserConfig"]` for clarity.

### Changed

- **CMakeProjectGenerator** now accepts `context` and `user_config` parameters, and passes context to template rendering (matching SkbuildProjectGenerator's pattern).

- **SkbuildProjectGenerator** now accepts an optional `user_config` parameter that merges user identity and defaults into the template context.

- **Template defaults are no longer hardcoded** - C++ templates read `defaults.cxx_standard` (fallback: 17), C templates read `defaults.c_standard` (fallback: 11), pyproject.toml templates read `defaults.license` (fallback: MIT) and `defaults.python_version` (fallback: 3.10).

## [0.1.9]

### Added

- **CLI Modularization** - Restructured CLI from single `cli.py` into a proper module (`cli/__init__.py`, `cli/commands.py`, `cli/main.py`, `cli/parsers.py`) for better maintainability and extensibility.

- **New Project Templates** - Added common templates for generated projects:
  - `CHANGELOG.md.mako` - Changelog template
  - `LICENSE.mako` - MIT license template
  - `gitignore.cmake.mako` - CMake project .gitignore
  - `gitignore.python.mako` - Python project .gitignore
  - GitHub workflow templates (`build-publish.yml.mako`, `ci.yml.mako`)

- **Python Extension Improvements**:
  - Added `py.typed` marker files to all Python extension templates (pybind11, nanobind, cython, cext) for PEP 561 compliance
  - Added base pyproject template (`pyproject.base.toml.mako`) for shared configuration

- **Enhanced Makefile Templates** - Expanded `Makefile.uv.mako` and `Makefile.venv.mako` with additional targets and improved functionality.

- **Comprehensive Test Suite**:
  - Added CLI tests (`tests/test_cli.py`) covering command parsing and execution
  - Added `UniqueList` tests (`tests/test_unique_list.py`)

### Fixed

- **Makefile variable handling** - Fixed bug in `makefile/variables.py` affecting variable generation.

## [0.1.8]

### Fixed

- **bug which caused crash of cli** -- due to missing subcmd.

## [0.1.7]

### Added

- **Recipe regression tests** - Added pytest coverage that instantiates every recipe, runs CMake builds for C/C++ templates, and keeps artifacts under `build/build-output/<test>/<recipe>/` for inspection.
- **Persistent build/test outputs** - Test session now resets both `build/test-output/` (legacy file-render fixtures) and the new `build/build-output/` folders before each run so inspection directories are always fresh.
- **Skbuild builds by default** - Recipe tests now run `uv sync` followed by `uv build` for Python extension templates automatically; pass `--skip-skbuild-build` to pytest when you need to opt out.
- **Pybind11-flex README** - The configurable recipe now generates a short `README.md` so scikit-build-core metadata parsing succeeds out of the box.
- **Pybind11-flex test harness defaults** - Automated regression tests disable the native Catch2/GTest harness (and CLI example) when rendering `py/pybind11-flex` so CI-only build toolchains without Catch2 can still compile the template.

### Changed

- **Pybind11-flex dev dependency floor lowered** - The generated `pybind11-stubgen` requirement now targets `>=0.14` so offline development environments (like CI mirrors) can satisfy it with the commonly mirrored 2.5.x releases.


## [0.1.6]

### Added

- **Configurable Flex Recipes** - `buildgen new <name> -r py/pybind11-flex` now emits a `project.flex.json` that describes toggleable options (env tool, native test framework, CLI example). After editing, run the new `buildgen render <config>` command to materialize the project; the renderer forwards the selected options into the templates so `pyproject.toml`, `CMakeLists.txt`, and generated sources reflect your choices.

### Changed

- **mako & pyyaml are now dependencies** - All of the features are available in one shot.

- **Plain Config Output After Render** - Rendering a flex config now produces a regular `project.json` inside the project (with placeholders resolved and `options` removed) while keeping the original `project.flex.json` alongside the config you edited. This keeps the configurable template for future edits without duplicating it in the generated project.

## [0.1.5]

### BREAKING CHANGES

- **CLI API Redesign** - The `project` command has been removed and replaced with simpler top-level commands:
  - `buildgen project init -n <name> -r <recipe>` -> `buildgen new <name> -r <recipe>`
  - `buildgen project recipes` -> `buildgen list`
  - `buildgen project generate -c <file>` -> `buildgen generate --from <file>`

### Added

- **Simplified CLI API** - New top-level commands replacing verbose nested subcommands
  - `buildgen new <name> [-r/--recipe]` - Create project from recipe (default: cpp/executable)
  - `buildgen list [-c/--category]` - List available recipes
  - `buildgen test [options]` - Test recipe generation and building
  - `buildgen generate --config FILE` - Generate boilerplate config file
  - `buildgen generate --from FILE` - Generate build files from existing config

- **Recipe Testing Command** (`buildgen test`)
  - `--name/-n` - Test specific recipe
  - `--category/-c` - Test all recipes in category
  - `--build/-b` - Build generated projects
  - `--test/-t` - Run project tests
  - `--all/-a` - Build and test (same as --build --test)
  - `--keep/-k` - Keep output after testing
  - `--output/-o` - Custom output directory

- **pytest in Python Extension Templates** - All py/* templates now include pytest>=8.0 in dev dependencies

### Changed

- Removed legacy `project` command (use `new`, `list`, `generate` instead)
- CLI examples in README updated to new simplified syntax

### Fixed

- **Cython template for scikit-build-core** - Replaced old scikit-build style (`find_package(Cython)`, `cython_transpile()`) with scikit-build-core compatible approach using `add_custom_command` and `Python::Interpreter -m cython`
- **py/cext recipe framework** - Changed from `framework="cext"` to `framework="c"` to match skbuild-c template

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
  - Each template includes: pyproject.toml, CMakeLists.txt, source files, **init**.py, tests

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
