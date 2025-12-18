# Changelog

All notable changes to this project will be documented in this file.

## [unreleased]

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
