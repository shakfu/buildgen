<%page args="name, options={}, defaults={}" />\
<%
raw_options = locals().get("options")
if not isinstance(raw_options, dict):
    raw_options = {}
opts = raw_options
_defaults = defaults if isinstance(defaults, dict) else {}
# The floor matches pyproject's requires-python (defaults.python_version); CI
# must not test below it. The newest leg is a recent release, clamped to >= floor.
min_python = opts.get("min_python", _defaults.get("python_version", "3.10"))
python_version = opts.get("python_version", "3.13")
_vt = lambda v: tuple(int(p) for p in v.split("."))
if _vt(python_version) < _vt(min_python):
    python_version = min_python
_matrix_versions = [min_python] if min_python == python_version else [min_python, python_version]
# pure_python: no compiled extension, so one wheel serves every platform and
# the build leg collapses to a single runner.
pure_python = bool(opts.get("pure_python", False))
_matrix_os = ["ubuntu-latest"] if pure_python else ["ubuntu-latest", "macos-latest", "windows-latest"]
_build_step = "Build wheel" if pure_python else "Build extension"
%>\
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: ci-${"${{ github.workflow }}"}-${"${{ github.ref }}"}
  cancel-in-progress: true

jobs:
  qa:
    name: QA (lint, typecheck, test)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - name: Install uv
        uses: astral-sh/setup-uv@v10
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install ${python_version}

      - name: Install dependencies
        run: uv sync --dev

      - name: Lint with ruff
        run: uv run ruff check src/ tests/

      - name: Check formatting with ruff
        run: uv run ruff format --check src/ tests/

      - name: Type check with mypy
        run: uv run mypy src/${name} tests/

      - name: Run tests
        run: uv run pytest tests/ -v --cov=src/${name} --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v7
        with:
          files: coverage.xml
          fail_ci_if_error: false
          token: ${"${{ secrets.CODECOV_TOKEN }}"}

  build:
    name: Build (${"${{ matrix.os }}"}/${"${{ matrix.python-version }}"})
    needs: qa
    runs-on: ${"${{ matrix.os }}"}
    strategy:
      fail-fast: false
      matrix:
        os: [${", ".join(_matrix_os)}]
        python-version: [${", ".join('"%s"' % v for v in _matrix_versions)}]

    steps:
      - uses: actions/checkout@v7

      - name: Install uv
        uses: astral-sh/setup-uv@v10
        with:
          enable-cache: true

      - name: Set up Python ${"${{ matrix.python-version }}"}
        run: uv python install ${"${{ matrix.python-version }}"}

      - name: Install dependencies
        run: uv sync

      - name: ${_build_step}
        run: uv build --wheel

      - name: Run tests
        run: uv run pytest tests/ -v

      - name: Upload wheel artifact
        uses: actions/upload-artifact@v7
        with:
          name: wheel-${"${{ matrix.os }}"}-py${"${{ matrix.python-version }}"}
          path: dist/*.whl
          retention-days: 7

  collect-artifacts:
    name: Collect all artifacts
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v8
        with:
          path: all-wheels
          pattern: wheel-*
          merge-multiple: true

      - name: List collected wheels
        run: ls -la all-wheels/

      - name: Upload combined artifacts
        uses: actions/upload-artifact@v7
        with:
          name: all-wheels
          path: all-wheels/
          retention-days: 14
