"""Tests for ${name} extension module."""

import ${name}


def test_add():
    """Test add function."""
    assert ${name}.add(1, 2) == 3
    assert ${name}.add(-1, 1) == 0
    assert ${name}.add(0, 0) == 0


def test_greet():
    """Test greet function."""
    assert ${name}.greet("World") == "Hello, World!"
    assert ${name}.greet("Python") == "Hello, Python!"
