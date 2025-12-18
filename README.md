# buildgen

A build system generator package supporting Makefile, CMake, and cross-generator project definitions.

Originally inspired by prior work on `shedskin.makefile` in the [shedskin project](https://github.com/shedskin/shedskin).

## Installation

```bash
pip install buildgen
```

## Quick Start

```bash
# Create a project config
buildgen project init -t full -n myproject -o project.json

# Generate both Makefile and CMakeLists.txt
buildgen project generate -c project.json --all

# Or generate CMake with Makefile frontend
buildgen project generate -c project.json --cmake
```

## Features

- **Makefile Generation**: Programmatic Makefile creation with variables, pattern rules, conditionals
- **CMake Generation**: Full CMakeLists.txt generation with find_package, FetchContent, install rules
- **Cross-Generator**: Define project once in JSON/YAML, generate both build systems
- **CMake Frontend**: Use CMake as build system with convenient Makefile wrapper
- **Project Templates**: Quick-start templates for common project types

## Usage

### CLI

```bash
# Project configuration workflow (recommended)
buildgen project init -t full -n myproject -o project.json
buildgen project generate -c project.json --all
buildgen project types  # List available templates

# Direct Makefile generation
buildgen makefile generate -o Makefile --targets "all:main.o:"
buildgen makefile build myprogram --cppfiles main.cpp

# Direct CMake generation
buildgen cmake generate -o CMakeLists.txt --project myapp --cxx-standard 17
buildgen cmake build -S . -B build --build-type Release
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

### Project Templates

```bash
buildgen project types
```

| Template | Description |
|----------|-------------|
| `executable` | Single executable (src/main.cpp) |
| `static` | Static library with include/ |
| `shared` | Shared library with -fPIC |
| `header-only` | Header-only/interface library |
| `library-with-tests` | Library + test executable |
| `app-with-lib` | Executable with internal library |
| `full` | Library + app + tests + Threads |

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
make test        # Run tests (194 tests)
make coverage    # Coverage report
```

## License

GPL-3.0-or-later
