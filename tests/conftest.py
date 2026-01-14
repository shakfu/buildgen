"""Pytest configuration and fixtures."""

import shutil
from pathlib import Path
from typing import Callable

import pytest

# Output directories for generated files
OUTPUT_DIR = Path(__file__).parent.parent / "build" / "test-output"
BUILD_OUTPUT_DIR = Path(__file__).parent.parent / "build" / "build-output"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register CLI options for the test suite."""
    parser.addoption(
        "--skip-skbuild-build",
        action="store_true",
        help="Skip uv sync and uv run python -m build for skbuild recipes.",
    )


@pytest.fixture(scope="session", autouse=True)
def _reset_output_dirs() -> None:
    """Remove persisted output directories at the start of the test session."""
    for directory in (OUTPUT_DIR, BUILD_OUTPUT_DIR):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def build_skbuild_enabled(pytestconfig: pytest.Config) -> bool:
    """Return False when the user opts out via --skip-skbuild-build."""
    return not bool(pytestconfig.getoption("--skip-skbuild-build"))


@pytest.fixture
def output_dir() -> Path:
    """Fixture providing the test output directory, creating it if needed."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


@pytest.fixture
def test_output_dir(output_dir: Path) -> Callable[[str], Path]:
    """Fixture providing a function to get/create test-specific output directories."""

    def get_test_dir(name: str) -> Path:
        test_dir = output_dir / name
        test_dir.mkdir(parents=True, exist_ok=True)
        return test_dir

    return get_test_dir


@pytest.fixture
def build_output_dir() -> Path:
    """Fixture providing the persistent build output directory."""
    BUILD_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return BUILD_OUTPUT_DIR


@pytest.fixture
def build_project_dir_factory(
    build_output_dir: Path, request: pytest.FixtureRequest
) -> Callable[[str], Path]:
    """Factory that returns unique subdirectories for each test."""

    def get_build_dir(name: str) -> Path:
        test_name = request.node.name
        safe_test_name = "".join(
            ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in test_name
        )
        target = build_output_dir / safe_test_name / name
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)
        return target

    return get_build_dir
