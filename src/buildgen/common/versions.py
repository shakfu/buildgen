"""Central registry of every version buildgen writes into generated projects.

One table per kind of pin. Templates read these tables instead of carrying
literals, so a bump happens here and nowhere else.

PyPI entries are floors that may be replaced at generation time by a live
lookup (``deps.resolve_latest_versions``) or by a user config ``[deps]`` pin;
the values here are the offline fallback. Every other table is the sole source
of the literal that lands in generated files.

Action refs are maintained by ``scripts/update_workflow_actions.py``, which
rewrites ``ACTIONS`` alongside this repo's own ``.github/workflows``.
"""

from __future__ import annotations

LOCK_VERSION = 1
PRESETS_SCHEMA_VERSION = 6

# PyPI floors for tools and build backends installed by generated projects.
PYPI: dict[str, str] = {
    "mypy": "2.3.1",
    "pytest": "9.1.1",
    "pytest-cov": "7.1.0",
    "ruff": "0.16.5",
    "twine": "7.0.0",
    "pybind11-stubgen": "2.5.5",
    "scikit-build-core": "1.0.3",
    "uv-build": "0.12.6",
}

# Packages whose floor is a compatibility constraint, not a freshness target.
BUILD_BACKENDS = frozenset({"scikit-build-core", "uv-build"})

# Dev-group tools, in the order they appear in a generated pyproject.toml.
DEV_TOOLS: tuple[str, ...] = ("mypy", "pytest", "pytest-cov", "ruff", "twine")

# PyPI distribution name -> name written into [build-system] requires, where
# the two differ. uv publishes `uv-build`; its documented build-system entry
# spells it `uv_build`, which is also the backend module name.
REQUIREMENT_NAMES: dict[str, str] = {"uv-build": "uv_build"}

# Packages requiring an upper bound at the next minor. uv-build follows uv's
# release train and its documented pin is `>=X.Y.Z,<X.Y+1`.
# https://docs.astral.sh/uv/concepts/build-backend/#choosing-a-build-backend
CAPPED_AT_NEXT_MINOR = frozenset({"uv-build"})

# GitHub Actions refs, shared by this repo's workflows and the generated ones.
ACTIONS: dict[str, str] = {
    "actions/checkout": "v7",
    "actions/download-artifact": "v8",
    "actions/upload-artifact": "v7",
    "astral-sh/setup-uv": "v10.0.1",
    "codecov/codecov-action": "v7",
    "docker/setup-qemu-action": "v4",
    "pypa/cibuildwheel": "v4.2",
    "pypa/gh-action-pypi-publish": "release/v1",
}

# cmake_minimum_required(VERSION <min>...<policy_max>). The Python extension
# floor is lower than the standalone C/C++ floor because scikit-build-core
# already constrains the CMake it provisions.
CMAKE: dict[str, str] = {
    "min": "3.16",
    "policy_max": "3.31",
    "python_ext_min": "3.15",
    "flex_min": "3.18",
}

# Language standard defaults for generated CMakeLists.txt.
STANDARDS: dict[str, int] = {"cxx": 17, "c": 11}

# floor: requires-python and the CI matrix's lower leg.
# ci_latest: the CI matrix's upper leg.
# max_classifier_minor: highest 3.x written as a Programming Language classifier.
PYTHON: dict[str, str | int] = {
    "floor": "3.10",
    "ci_latest": "3.13",
    "max_classifier_minor": 14,
}

# FetchContent GIT_TAG values for native test frameworks.
GIT_TAGS: dict[str, str] = {
    "catch2": "v3.5.3",
    "googletest": "v1.14.0",
}


def next_minor(version: str) -> str:
    """Return *version* with its minor incremented and the patch dropped.

    ``"0.12.6"`` -> ``"0.13"``. Raises ValueError if *version* has no minor.
    """
    parts = version.split(".")
    if len(parts) < 2:
        raise ValueError(f"version has no minor component: {version!r}")
    return f"{parts[0]}.{int(parts[1]) + 1}"


def requirement(package: str, versions: dict[str, str] | None = None) -> str:
    """Return the PEP 508 requirement string for *package*.

    Reads the version from *versions* (falling back to PYPI), maps the
    distribution name through REQUIREMENT_NAMES, and adds the next-minor upper
    bound for packages in CAPPED_AT_NEXT_MINOR.
    """
    table = versions or PYPI
    version = table.get(package) or PYPI.get(package, "0")
    name = REQUIREMENT_NAMES.get(package, package)
    if package in CAPPED_AT_NEXT_MINOR:
        return f"{name}>={version},<{next_minor(version)}"
    return f"{name}>={version}"


def action(name: str) -> str:
    """Return the ``owner/repo@ref`` string for a pinned GitHub Action."""
    return f"{name}@{ACTIONS[name]}"
