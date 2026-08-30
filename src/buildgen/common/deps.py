"""Dependency version resolution for generated projects.

Resolves latest package versions from PyPI at generation time,
with fallback to bundled defaults when offline or on error.
"""

import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from buildgen.common import versions

# Fallback versions used when PyPI is unreachable or --no-update-deps is set.
# The table itself lives in versions.py with every other pin buildgen writes.
DEFAULT_VERSIONS = versions.PYPI

# Packages whose version floor is a compatibility constraint, not a freshness
# target.  resolve_latest_versions() still updates them, but callers can
# choose to treat them differently.
BUILD_SYSTEM_PACKAGES = versions.BUILD_BACKENDS

_PYPI_URL = "https://pypi.org/pypi/{}/json"
# Kept short: this runs on the generation path, the fallback is always correct,
# and a PyPI that has not answered in two seconds is not worth waiting on.
_TIMEOUT = 2  # seconds per request
# Requests are independent, so the offline worst case is one timeout rather
# than one per package.
_MAX_WORKERS = 8


def _fetch_latest_version(package: str) -> str | None:
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
    packages: list[str] | None = None,
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
        for pkg, found in zip(packages, latest, strict=False)
    }


def get_default_versions(
    packages: list[str] | None = None,
) -> dict[str, str]:
    """Return the bundled default versions (no network)."""
    if packages is None:
        return dict(DEFAULT_VERSIONS)
    return {pkg: DEFAULT_VERSIONS.get(pkg, "0") for pkg in packages}


def load_lock(path: Path) -> dict[str, Any]:
    """Load a buildgen lock file and validate its top-level shape."""
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("dependencies", {}), dict):
        raise ValueError(f"Invalid buildgen lock file: {path}")  # noqa: TRY004
    lock_version = data.get("lock_version")
    if lock_version != versions.LOCK_VERSION:
        raise ValueError(
            f"Unsupported buildgen lock version {lock_version!r} in {path}: "
            f"this buildgen writes version {versions.LOCK_VERSION}"
        )
    return data


def write_lock(
    path: Path,
    *,
    recipe: str,
    dependencies: dict[str, str],
    buildgen_version: str,
    inputs: dict[str, Any] | None = None,
) -> None:
    """Write a deterministic project-local dependency lock."""
    data = {
        "lock_version": versions.LOCK_VERSION,
        "buildgen_version": buildgen_version,
        "recipe": recipe,
        "inputs": inputs or {},
        "dependencies": dict(sorted(dependencies.items())),
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
