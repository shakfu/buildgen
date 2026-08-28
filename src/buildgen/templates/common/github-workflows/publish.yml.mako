<%page args="name, options={}, defaults={}" />\
<%!
from buildgen.common import versions as V
%>\
name: Publish

on:
  push:
    tags:
      - "v*"
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
  group: publish-${"${{ github.workflow }}"}-${"${{ github.ref }}"}
  cancel-in-progress: false

jobs:
  build:
    name: Build sdist and wheel
    runs-on: ubuntu-latest
    steps:
      - uses: ${V.action('actions/checkout')}

      - name: Install uv
        uses: ${V.action('astral-sh/setup-uv')}
        with:
          enable-cache: true

      - name: Build distributions
        run: uv build

      - name: Check distributions
        run: uvx twine check dist/*

      - name: Upload distributions
        uses: ${V.action('actions/upload-artifact')}
        with:
          name: dist
          path: dist/
          retention-days: 14

  publish-testpypi:
    name: Publish to TestPyPI
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
    environment:
      name: testpypi
      url: https://test.pypi.org/p/${name}
    permissions:
      id-token: write
    steps:
      - name: Download distributions
        uses: ${V.action('actions/download-artifact')}
        with:
          name: dist
          path: dist/

      - name: Publish to TestPyPI
        uses: ${V.action('pypa/gh-action-pypi-publish')}
        with:
          repository-url: https://test.pypi.org/legacy/
          skip-existing: true

  publish-pypi:
    name: Publish to PyPI
    needs: [build, publish-testpypi]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
    environment:
      name: pypi
      url: https://pypi.org/p/${name}
    permissions:
      id-token: write
    steps:
      - name: Download distributions
        uses: ${V.action('actions/download-artifact')}
        with:
          name: dist
          path: dist/

      - name: Publish to PyPI
        uses: ${V.action('pypa/gh-action-pypi-publish')}

  publish-manual:
    name: Manual publish to PyPI
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'workflow_dispatch' && inputs.publish
    environment:
      name: pypi
      url: https://pypi.org/p/${name}
    permissions:
      id-token: write
    steps:
      - name: Download distributions
        uses: ${V.action('actions/download-artifact')}
        with:
          name: dist
          path: dist/

      - name: Publish to PyPI
        uses: ${V.action('pypa/gh-action-pypi-publish')}
