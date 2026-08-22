"""Dependency version resolution for generated projects.

Resolves latest package versions from PyPI at generation time,
with fallback to bundled defaults when offline or on error.
"""

import json
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from typing import Optional


# Fallback versions used when PyPI is unreachable or --no-update-deps is set.
# Keep these reasonably current -- they're the floor, not the ceiling.
DEFAULT_VERSIONS: dict[str, str] = {
    "mypy": "1.19.1",
    "pytest": "8.4.2",
    "pytest-cov": "7.0.0",
    "ruff": "0.14.9",
    "twine": "7.0.0",
    "pybind11-stubgen": "0.14",
    "scikit-build-core": "0.12",
    "hatchling": "1.27.0",
}

# Packages whose version floor is a compatibility constraint, not a freshness
# target.  resolve_latest_versions() still updates them, but callers can
# choose to treat them differently.
BUILD_SYSTEM_PACKAGES = frozenset({"scikit-build-core", "hatchling"})

_PYPI_URL = "https://pypi.org/pypi/{}/json"
# Kept short: this runs on the generation path, the fallback is always correct,
# and a PyPI that has not answered in two seconds is not worth waiting on.
_TIMEOUT = 2  # seconds per request
# Requests are independent, so the offline worst case is one timeout rather
# than one per package.
_MAX_WORKERS = 8


def _fetch_latest_version(package: str) -> Optional[str]:
    """Query PyPI for the latest release version of *package*.

    Returns None on any network or parse error.
    """
    url = _PYPI_URL.format(package)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read())
            return data["info"]["version"]
    except (urllib.error.URLError, OSError, KeyError, json.JSONDecodeError):
        return None


def resolve_latest_versions(
    packages: Optional[list[str]] = None,
) -> dict[str, str]:
    """Resolve the latest PyPI versions for *packages*.

    For each package, queries PyPI and falls back to DEFAULT_VERSIONS on
    failure.  If *packages* is None, resolves all packages in
    DEFAULT_VERSIONS.
    """
    if packages is None:
        packages = list(DEFAULT_VERSIONS.keys())
    if not packages:
        return {}

    workers = min(_MAX_WORKERS, len(packages))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        latest = list(pool.map(_fetch_latest_version, packages))

    # Built in the caller's package order so output stays deterministic.
    return {
        pkg: found if found is not None else DEFAULT_VERSIONS.get(pkg, "0")
        for pkg, found in zip(packages, latest)
    }


def get_default_versions(
    packages: Optional[list[str]] = None,
) -> dict[str, str]:
    """Return the bundled default versions (no network)."""
    if packages is None:
        return dict(DEFAULT_VERSIONS)
    return {pkg: DEFAULT_VERSIONS.get(pkg, "0") for pkg in packages}
