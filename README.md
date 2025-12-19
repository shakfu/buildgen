# buildgen

A zero-dependency[^1] build system generator package supporting Makefile, CMake, and cross-generator project definitions.

Originally inspired by prior work on `shedskin.makefile` in the [shedskin project](https://github.com/shedskin/shedskin).

[^1]: uses an embedded *lite* version of [Mako Templates](https://www.makotemplates.org/)

## Installation

```bash
pip install buildgen
```

## Quick Start

```bash
# Create a C++ project
buildgen project init -n myapp --recipe cpp/executable

# Create a Python extension with pybind11
buildgen project init -n myext --recipe py/pybind11

# List available recipes
buildgen project recipes
```

## Features

- **Makefile Generation**: Programmatic Makefile creation with variables, pattern rules, conditionals
- **CMake Generation**: Full CMakeLists.txt generation with find_package, FetchContent, install rules
- **Cross-Generator**: Define project once in JSON/YAML, generate both build systems
- **CMake Frontend**: Use CMake as build system with convenient Makefile frontend
- **Project Templates**: Quick-start templates for common project types
- **scikit-build-core Templates**: Python extension project scaffolding (pybind11, cython, nanobind, C)
- **Template Customization**: Override templates per-project, per-user, or via environment variable (Mako syntax)

## Usage

### CLI

```bash
# Create projects from recipes
buildgen project init -n myapp --recipe cpp/executable
buildgen project init -n mylib --recipe c/static
buildgen project init -n myext --recipe py/pybind11

# Short form
buildgen project init -n myapp -r cpp/full

# List available recipes
buildgen project recipes

# Direct Makefile generation
buildgen makefile generate -o Makefile --targets "all:main.o:"

# Direct CMake generation
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

### Project Recipes

Recipes use a `category/variant` naming convention:

```bash
buildgen project recipes
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
| `py/nanobind` | C++ extension using nanobind |
| `py/cython` | Extension using Cython |
| `py/cext` | C extension (Python.h) |

### Python Extension Projects

Generate complete Python extension projects with scikit-build-core:

```bash
# Create a pybind11 extension project
buildgen project init -n myext --recipe py/pybind11

# Use traditional virtualenv instead of uv
buildgen project init -n myext --recipe py/pybind11 --env venv
```

This creates a complete project structure:

```
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
   buildgen project init -n myext --recipe py/pybind11
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
