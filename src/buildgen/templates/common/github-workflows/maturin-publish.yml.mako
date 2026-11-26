<%page args="name, options={}, defaults={}" />\
<%!
from buildgen.common import versions as V
from buildgen.skbuild.maturin import resolve
%>\
<%
_defaults = defaults if isinstance(defaults, dict) else {}
_m = resolve(options)
min_python = _defaults.get("python_version", str(V.PYTHON["floor"]))
max_python = str(V.PYTHON["ci_latest"])
# abi3, cffi, and uniffi wheels do not depend on the CPython minor version, so
# one wheel per platform suffices. Plain pyo3 needs one per interpreter.
_per_version = _m.bindings == "pyo3" and not _m.abi3
_minors = range(int(min_python.split(".")[1]), max(int(max_python.split(".")[1]), int(min_python.split(".")[1])) + 1)
_pythons = [f"3.{v}" for v in _minors] if _per_version else [min_python]
_args = "--release --out dist" + (" --find-interpreter" if _per_version else "")
%>\
# Platform matrix follows `maturin generate-ci github`, trimmed to the targets
# the other buildgen extension recipes publish.
name: Build and Publish

on:
  push:
    tags:
      - "v*"
  pull_request:
    branches: [main, master]
  workflow_dispatch:
    inputs:
      publish:
        description: "Publish to PyPI"
        required: false
        default: false
        type: boolean

permissions:
  contents: read

concurrency:
  group: build-${"${{ github.workflow }}"}-${"${{ github.ref }}"}
  cancel-in-progress: true

jobs:
  build-sdist:
    name: Build source distribution
    runs-on: ubuntu-latest
    steps:
      - uses: ${V.action('actions/checkout')}

      - name: Build sdist
        uses: ${V.action('PyO3/maturin-action')}
        with:
          command: sdist
          args: --out dist

      - name: Upload sdist
        uses: ${V.action('actions/upload-artifact')}
        with:
          name: dist-sdist
          path: dist/*.tar.gz
          retention-days: 14

  build-wheels:
    name: Build wheels (${"${{ matrix.runner }}"}/${"${{ matrix.target }}"})
    runs-on: ${"${{ matrix.runner }}"}
    strategy:
      fail-fast: false
      matrix:
        include:
          - { runner: ubuntu-latest, target: x86_64 }
          - { runner: ubuntu-latest, target: aarch64 }
          - { runner: macos-latest, target: x86_64 }
          - { runner: macos-latest, target: aarch64 }
          - { runner: windows-latest, target: x64 }
    steps:
      - uses: ${V.action('actions/checkout')}

      - uses: ${V.action('actions/setup-python')}
        with:
% if len(_pythons) == 1:
          python-version: "${_pythons[0]}"
% else:
          python-version: |
% for _v in _pythons:
            ${_v}
% endfor
% endif

      - name: Build wheels
        uses: ${V.action('PyO3/maturin-action')}
        with:
          target: ${"${{ matrix.target }}"}
          args: ${_args}
          sccache: ${"${{ !startsWith(github.ref, 'refs/tags/') }}"}
          manylinux: auto

      - name: Upload wheels
        uses: ${V.action('actions/upload-artifact')}
        with:
          name: dist-${"${{ matrix.runner }}"}-${"${{ matrix.target }}"}
          path: dist/*.whl
          retention-days: 14

  collect-artifacts:
    name: Collect all build artifacts
    needs: [build-sdist, build-wheels]
    runs-on: ubuntu-latest
    steps:
      - name: Download all artifacts
        uses: ${V.action('actions/download-artifact')}
        with:
          pattern: dist-*
          path: dist/
          merge-multiple: true

      - name: List all artifacts
        run: ls -la dist/

      - name: Upload combined artifacts
        uses: ${V.action('actions/upload-artifact')}
        with:
          name: all-dist
          path: dist/
          retention-days: 30

  publish-testpypi:
    name: Publish to TestPyPI
    needs: collect-artifacts
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
    environment:
      name: testpypi
      url: https://test.pypi.org/p/${name}
    permissions:
      id-token: write
    steps:
      - name: Download all artifacts
        uses: ${V.action('actions/download-artifact')}
        with:
          name: all-dist
          path: dist/

      - name: Publish to TestPyPI
        uses: ${V.action('pypa/gh-action-pypi-publish')}
        with:
          repository-url: https://test.pypi.org/legacy/
          skip-existing: true

  publish-pypi:
    name: Publish to PyPI
    needs: [collect-artifacts, publish-testpypi]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
    environment:
      name: pypi
      url: https://pypi.org/p/${name}
    permissions:
      id-token: write
    steps:
      - name: Download all artifacts
        uses: ${V.action('actions/download-artifact')}
        with:
          name: all-dist
          path: dist/

      - name: Publish to PyPI
        uses: ${V.action('pypa/gh-action-pypi-publish')}

  publish-manual:
    name: Manual Publish to PyPI
    needs: collect-artifacts
    runs-on: ubuntu-latest
    if: github.event_name == 'workflow_dispatch' && inputs.publish
    environment:
      name: pypi
      url: https://pypi.org/p/${name}
    permissions:
      id-token: write
    steps:
      - name: Download all artifacts
        uses: ${V.action('actions/download-artifact')}
        with:
          name: all-dist
          path: dist/

      - name: Publish to PyPI
        uses: ${V.action('pypa/gh-action-pypi-publish')}
