"""Pytest configuration and fixtures."""

from pathlib import Path
from typing import Callable

import pytest

# Output directory for all generated files
OUTPUT_DIR = Path(__file__).parent.parent / "build" / "test-output"


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
