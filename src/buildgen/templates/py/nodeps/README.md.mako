# ${name}

A pure-Python package with no runtime dependencies.

${"##"} Quick Start

```bash
uv sync
uv run pytest
uv build
```

Everything ships as a single pure-Python wheel -- no compiler, no CMake, and no
third-party packages at runtime. Development tooling (pytest, ruff, mypy) lives
in the `dev` dependency group and is not part of the published distribution.

Use `make help` for additional targets (wheel, sdist, clean, etc.).
