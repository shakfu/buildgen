"""Tests for ${name}."""

import ${name}


def test_add() -> None:
    """Test add function."""
    assert ${name}.add(1, 2) == 3
    assert ${name}.add(-1, 1) == 0
    assert ${name}.add(0, 0) == 0


def test_greet() -> None:
    """Test greet function."""
    assert ${name}.greet("World") == "Hello, World!"
    assert ${name}.greet("Python") == "Hello, Python!"


def test_has_no_runtime_dependencies() -> None:
    """The distribution must not declare runtime dependencies."""
    from importlib.metadata import requires

    assert not (requires("${name}") or [])
