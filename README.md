# buildgen - generate your build-system

A build system generator package supporting Makefile, CMake, and [scikit-build-core](https://github.com/scikit-build/scikit-build-core) project definitions.

**Note**: the buildgen test suite generates, build and tests every one of its recipes.

## Installation

```bash
pip install buildgen
```

## Quick Start

```bash
# Create a C++ project
buildgen new myapp

# Create a Python extension with pybind11
buildgen new myext -r py/pybind11

# List available recipes
buildgen list
```

## Features

- **Makefile Generation**: Programmatic Makefile creation with variables, pattern rules, conditionals
- **CMake Generation**: Full CMakeLists.txt generation with find_package, FetchContent, install rules
- **Cross-Generator**: Define project recipes once in JSON/YAML, generate build systems
- **CMake Frontend**: Use CMake as build system with convenient Makefile frontend
- **Project Templates**: Quick-start templates for common project types
- **scikit-build-core Templates**: Python extension project scaffolding (pybind11, cython, nanobind, C)
- **Template Customization**: Override templates per-project, per-user, or via environment variable (Mako syntax)
- **Configurable Project Recipes**: 2-step JSON/YAML recipes which include options and which are `rendered` to generate the project infrastructure.
- **User Configuration**: Global `~/.buildgen/config.toml` for author identity and project defaults (license, language standards, Python version, env tool)

## Usage

### CLI

```bash
# Create projects from recipes
buildgen new myapp -r cpp/executable
buildgen new mylib -r c/static
buildgen new myext -r py/pybind11

# List available recipes
buildgen list

# Generate build files from a config file
buildgen generate --from project.json

# Test recipe generation and building
buildgen test --all

# Direct Makefile generation (advanced)
buildgen makefile generate -o Makefile --targets "all:main.o:"

# Direct CMake generation (advanced)
buildgen cmake generate -o CMakeLists.txt --project myapp --cxx-standard 17
```

### Python API

```python
from buildgen import ProjectConfig, TargetConfig, DependencyConfig

# Load from config file
config = ProjectConfig.load("project.json")
config.generate_all()  # Creates Makefile and CMakeLists.txt

# Or build programmatically
config = ProjectConfig(
    name="myproject",
    version="1.0.0",
    cxx_standard=17,
    compile_options=["-Wall", "-Wextra"],
    dependencies=[
        DependencyConfig(name="Threads"),
        DependencyConfig(
            name="fmt",
            git_repository="https://github.com/fmtlib/fmt.git",
            git_tag="10.1.1",
        ),
    ],
    targets=[
        TargetConfig(
            name="mylib",
            target_type="static",
            sources=["src/lib.cpp"],
            include_dirs=["include"],
        ),
        TargetConfig(
            name="myapp",
            target_type="executable",
            sources=["src/main.cpp"],
            link_libraries=["mylib", "fmt::fmt"],
            install=True,
        ),
    ],
)
config.generate_all()
```

### CMake with Makefile Frontend

Generate CMake as the build system with a Makefile that wraps cmake commands:

```python
config.generate_cmake_with_frontend(
    build_dir="build",
    build_type="Release",
)
```

This creates:

- `CMakeLists.txt` - The actual build logic
- `Makefile` - Convenience wrapper with targets:

```bash
make              # Configure and build
make build        # Same as above
make configure    # Run cmake configure only
make clean        # Remove build directory
make rebuild      # Clean and rebuild
make install      # Install the project
make test         # Run tests with ctest
make myapp        # Build specific target
make help         # Show available targets

# Override defaults
make BUILD_TYPE=Debug
make BUILD_DIR=cmake-build
make CMAKE_FLAGS="-DFOO=bar"
```

## Project Configuration

### JSON Format

```json
{
    "name": "myproject",
    "version": "1.0.0",
    "cxx_standard": 17,
    "compile_options": ["-Wall", "-Wextra"],
    "dependencies": [
        "Threads",
        {"name": "OpenSSL", "required": true},
        {
            "name": "fmt",
            "git_repository": "https://github.com/fmtlib/fmt.git",
            "git_tag": "10.1.1"
        }
    ],
    "targets": [
        {
            "name": "mylib",
            "type": "static",
            "sources": ["src/lib.cpp"],
            "include_dirs": ["include"],
            "install": true
        },
        {
            "name": "myapp",
            "type": "executable",
            "sources": ["src/main.cpp"],
            "link_libraries": ["mylib", "Threads::Threads"],
            "install": true
        }
    ]
}
```

### YAML Format

```yaml
name: myproject
version: 1.0.0
cxx_standard: 17

compile_options:
  - -Wall
  - -Wextra

dependencies:
  - Threads
  - name: OpenSSL
    required: true
  - name: fmt
    git_repository: https://github.com/fmtlib/fmt.git
    git_tag: 10.1.1

targets:
  - name: mylib
    type: static
    sources:
      - src/lib.cpp
    include_dirs:
      - include
    install: true

  - name: myapp
    type: executable
    sources:
      - src/main.cpp
    link_libraries:
      - mylib
      - Threads::Threads
    install: true
```

### Project Recipes

Recipes use a `category/variant` naming convention:

```bash
buildgen list
```

**C++ Recipes** (CMake + Makefile frontend):

| Recipe | Description |
|--------|-------------|
| `cpp/executable` | Single executable |
| `cpp/static` | Static library |
| `cpp/shared` | Shared library (-fPIC) |
| `cpp/header-only` | Header-only library |
| `cpp/library-with-tests` | Library + tests |
| `cpp/app-with-lib` | App with internal library |
| `cpp/full` | Library + app + tests |

**C Recipes** (CMake + Makefile frontend):

| Recipe | Description |
|--------|-------------|
| `c/executable` | Single executable |
| `c/static` | Static library |
| `c/shared` | Shared library (-fPIC) |
| `c/header-only` | Header-only library |
| `c/library-with-tests` | Library + tests |
| `c/app-with-lib` | App with internal library |
| `c/full` | Library + app + tests |

**Python Extension Recipes** (scikit-build-core):

| Recipe | Description |
|--------|-------------|
| `py/pybind11` | C++ extension using pybind11 |
| `py/pybind11-flex` | Pybind11 extension with optional Catch2/GTest tests + CLI |
| `py/nanobind` | C++ extension using nanobind |
| `py/cython` | Extension using Cython |
| `py/cext` | C extension (Python.h) |

### Python Extension Projects

Generate complete Python extension projects with scikit-build-core:

```bash
# Create a pybind11 extension project
buildgen new myext -r py/pybind11

# Use traditional virtualenv instead of uv
buildgen new myext -r py/pybind11 --env venv
```

This creates a complete project structure:

```text
myext/
  pyproject.toml      # scikit-build-core configuration
  CMakeLists.txt      # CMake build instructions
  Makefile            # Convenience wrapper
  src/myext/
    __init__.py       # Python package
    _core.cpp         # C++ extension source
  tests/
    test_myext.py     # pytest tests
```

The generated Makefile provides convenient commands (using `uv` by default):

```bash
make sync     # Initial setup (uv sync)
make build    # Rebuild extension after code changes
make test     # Run tests (uv run pytest)
make wheel    # Build wheel distribution
make clean    # Remove build artifacts
```

For traditional virtualenv workflows, use `--env venv` to generate pip/python commands instead.

The `py/pybind11-flex` recipe additionally drops a `project.flex.json` that documents
how to toggle the native Catch2/GTest harness and the optional embedded CLI using
`cmake -D` flags. Update its `options` block and rerun `cmake` to explore
different combinations without re-running `buildgen new`.

### Configurable Recipe Workflow

For recipes marked as configurable (like `py/pybind11-flex`), project creation is a
two-step flow:

```bash
buildgen new myflex -r py/pybind11-flex      # emits myflex/project.flex.json
# edit myflex/project.flex.json (env, test framework, CLI toggle)
buildgen render myflex/project.flex.json     # renders full project based on options
```

`buildgen render` produces a standard config (`project.json` or `.yaml`, depending on the
source filename) inside the generated project with all placeholders resolved, while the
original `project.flex.json` stays wherever you edited it for future re-runs. You can run
`buildgen render` from within the project directory as long as you point to the flex file.
Use `--env venv` on `buildgen render` to override the config’s environment choice without
editing the JSON/YAML.

## User Configuration

Set your identity and project defaults globally via `~/.buildgen/config.toml`:

```bash
# Create the config file with a commented template
buildgen config init

# View current config
buildgen config show

# Print config file path
buildgen config path
```

### Config Format

```toml
[user]
name = "Your Name"
email = "you@example.com"

[defaults]
license = "MIT"
cxx_standard = 17
c_standard = 11
python_version = "3.10"
env_tool = "uv"
```

### What the config affects

- **`user.name`** / **`user.email`** -- Populates the LICENSE copyright holder and `[[project.authors]]` in generated `pyproject.toml` files.
- **`defaults.license`** -- Sets the license identifier in `pyproject.toml` (default: `MIT`).
- **`defaults.cxx_standard`** -- Sets `CMAKE_CXX_STANDARD` in C++ CMakeLists.txt templates (default: `17`).
- **`defaults.c_standard`** -- Sets `CMAKE_C_STANDARD` in C CMakeLists.txt templates (default: `11`).
- **`defaults.python_version`** -- Sets `requires-python` in `pyproject.toml` (default: `3.10`).
- **`defaults.env_tool`** -- Fallback environment tool (`uv` or `venv`) when `--env` is not explicitly passed on the command line.

All defaults are optional. Without a config file, templates use their built-in fallback values.

## Template Customization

Templates can be customized without modifying buildgen. Override files are resolved in this order (first match wins):

1. `$BUILDGEN_TEMPLATES/{recipe}/` - Environment variable (for CI/CD)
2. `.buildgen/templates/{recipe}/` - Project-local overrides
3. `~/.buildgen/templates/{recipe}/` - User-global defaults
4. Built-in templates

### Template Commands

```bash
# List available templates and show which have overrides
buildgen templates list

# Copy templates for local customization
buildgen templates copy py/pybind11

# Copy to global location for user-wide defaults
buildgen templates copy py/pybind11 --global

# Show where each template file is resolved from
buildgen templates show py/pybind11
```

### Customizing Templates

1. Copy the templates you want to customize:

   ```bash
   buildgen templates copy py/pybind11
   ```

2. Edit the `.mako` files in `.buildgen/templates/py/pybind11/`:

   ```bash
   # Customize pyproject.toml template
   edit .buildgen/templates/py/pybind11/pyproject.toml.mako
   ```

3. Generate projects - your customizations will be used:

   ```bash
   buildgen new myext -r py/pybind11
   ```

Templates use [Mako](https://www.makotemplates.org/) syntax with `${variable}` for substitution.

### Per-File Overrides

You can override individual files while keeping others from built-in templates. For example, to customize only `pyproject.toml`:

```bash
mkdir -p .buildgen/templates/py/pybind11
cp $(buildgen templates show py/pybind11 | grep pyproject) .buildgen/templates/py/pybind11/
# Edit your local copy
```

## Low-Level API

For fine-grained control, use the generators directly:

```python
from buildgen import MakefileGenerator, CMakeListsGenerator

# Makefile
gen = MakefileGenerator("Makefile")
gen.add_cxxflags("-Wall", "-std=c++17")
gen.add_target("myapp", "$(CXX) $(CXXFLAGS) -o $@ $^", deps=["main.o"])
gen.add_pattern_rule("%.o", "%.cpp", "$(CXX) $(CXXFLAGS) -c $< -o $@")
gen.add_phony("all", "clean")
gen.generate()

# CMake
gen = CMakeListsGenerator("CMakeLists.txt")
gen.set_project("myapp", version="1.0.0")
gen.set_cxx_standard(17)
gen.add_find_package("Threads", required=True)
gen.add_executable("myapp", ["src/main.cpp"], link_libraries=["Threads::Threads"])
gen.generate()
```

## Development

```bash
make test        # Run tests
make lint        # Run ruff check
make coverage    # Coverage report
```

## Credits

- Template rendering powered by an embedded version of [Mako Templates](https://www.makotemplates.org/) (MIT License)
- Originally inspired by prior work in `shedskin.makefile` in the [shedskin project](https://github.com/shedskin/shedskin)

## License

GPL-3.0-or-later
