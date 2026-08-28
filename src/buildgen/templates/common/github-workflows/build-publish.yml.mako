<%page args="name, options={}, defaults={}" />\
<%!
from buildgen.common import versions as V
%>\
<%
raw_options = locals().get("options")
if not isinstance(raw_options, dict):
    raw_options = {}
opts = raw_options
_defaults = defaults if isinstance(defaults, dict) else {}
# The floor matches pyproject's requires-python (defaults.python_version).
min_python = opts.get("min_python", _defaults.get("python_version", str(V.PYTHON["floor"])))
max_python = opts.get("max_python", str(V.PYTHON["ci_latest"]))
# Build CPython versions from min to max
min_ver = int(min_python.split(".")[-1])
max_ver = int(max_python.split(".")[-1])
if max_ver < min_ver:
    max_ver = min_ver
cp_versions = " ".join(f"cp3{v}-*" for v in range(min_ver, max_ver + 1))
%>\
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

env:
  CIBW_BUILD: "${cp_versions}"
  CIBW_SKIP: "*-musllinux_* pp*"
  CIBW_TEST_REQUIRES: pytest
  CIBW_TEST_COMMAND: pytest {project}/tests -v

jobs:
  build-sdist:
    name: Build source distribution
    runs-on: ubuntu-latest
    steps:
      - uses: ${V.action('actions/checkout')}

      - name: Install uv
        uses: ${V.action('astral-sh/setup-uv')}

      - name: Build sdist
        run: uv build --sdist

      - name: Upload sdist
        uses: ${V.action('actions/upload-artifact')}
        with:
          name: sdist
          path: dist/*.tar.gz
          retention-days: 14

  build-wheels-linux:
    name: Build wheels (Linux)
    runs-on: ubuntu-latest
    steps:
      - uses: ${V.action('actions/checkout')}

      - name: Set up QEMU
        uses: ${V.action('docker/setup-qemu-action')}
        with:
          platforms: arm64

      - name: Build wheels
        uses: ${V.action('pypa/cibuildwheel')}
        env:
          CIBW_ARCHS_LINUX: x86_64 aarch64

      - name: Upload wheels
        uses: ${V.action('actions/upload-artifact')}
        with:
          name: wheels-linux
          path: wheelhouse/*.whl
          retention-days: 14

  build-wheels-macos:
    name: Build wheels (macOS)
    runs-on: macos-latest
    steps:
      - uses: ${V.action('actions/checkout')}

      - name: Build wheels
        uses: ${V.action('pypa/cibuildwheel')}
        env:
          CIBW_ARCHS_MACOS: x86_64 arm64

      - name: Upload wheels
        uses: ${V.action('actions/upload-artifact')}
        with:
          name: wheels-macos
          path: wheelhouse/*.whl
          retention-days: 14

  build-wheels-windows:
    name: Build wheels (Windows)
    runs-on: windows-latest
    steps:
      - uses: ${V.action('actions/checkout')}

      - name: Build wheels
        uses: ${V.action('pypa/cibuildwheel')}
        env:
          CIBW_ARCHS_WINDOWS: AMD64

      - name: Upload wheels
        uses: ${V.action('actions/upload-artifact')}
        with:
          name: wheels-windows
          path: wheelhouse/*.whl
          retention-days: 14

  collect-artifacts:
    name: Collect all build artifacts
    needs: [build-sdist, build-wheels-linux, build-wheels-macos, build-wheels-windows]
    runs-on: ubuntu-latest
    steps:
      - name: Download sdist
        uses: ${V.action('actions/download-artifact')}
        with:
          name: sdist
          path: dist/

      - name: Download Linux wheels
        uses: ${V.action('actions/download-artifact')}
        with:
          name: wheels-linux
          path: dist/

      - name: Download macOS wheels
        uses: ${V.action('actions/download-artifact')}
        with:
          name: wheels-macos
          path: dist/

      - name: Download Windows wheels
        uses: ${V.action('actions/download-artifact')}
        with:
          name: wheels-windows
          path: dist/

      - name: List all artifacts
        run: |
          echo "=== All build artifacts ==="
          ls -la dist/
          echo ""
          echo "=== Wheel count: $(ls dist/*.whl 2>/dev/null | wc -l) ==="
          echo "=== Sdist count: $(ls dist/*.tar.gz 2>/dev/null | wc -l) ==="

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
