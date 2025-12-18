# buildgen

A build system generator package supporting Makefile, CMake, and cross-generator project definitions.

Originally inspired by work on `shedskin.makefile` in the [shedskin project](https://github.com/shedskin/shedskin).

## Installation

```bash
pip install buildgen
```

## Usage

### CLI

```bash
# Generate from project config (recommended)
buildgen project init -t full -n myproject -o project.json
buildgen project generate -c project.json --all

# List available project templates
buildgen project types

# Direct Makefile generation
buildgen makefile generate -o Makefile --targets "all:main.o:"

# Direct CMake generation
buildgen cmake generate -o CMakeLists.txt --project myapp --cxx-standard 17
```

### Python API

```python
from buildgen import ProjectConfig, MakefileGenerator, CMakeListsGenerator

# Cross-generator: define once, generate both
config = ProjectConfig.load("project.json")
config.generate_all()  # Creates Makefile and CMakeLists.txt

# Or use generators directly
gen = MakefileGenerator("Makefile")
gen.add_include_dirs("include")
gen.add_target("all", deps=["main.o"])
gen.generate()
```

## Project Configuration

Define a project in JSON or YAML:

```json
{
    "name": "myproject",
    "version": "1.0.0",
    "cxx_standard": 17,
    "compile_options": ["-Wall", "-Wextra"],
    "targets": [
        {"name": "myapp", "type": "executable", "sources": ["src/main.cpp"]}
    ]
}
```

See `buildgen project types` for available templates.

## Development

```bash
make test        # Run tests
make coverage    # Coverage report
```

## License

MIT
