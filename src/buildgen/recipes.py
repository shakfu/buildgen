"""Recipe registry for buildgen project templates.

Recipes use a `category/variant` naming convention:
- cpp/executable, cpp/static, cpp/shared, etc.
- c/executable, c/static, c/shared, etc.
- py/pybind11, py/nanobind, py/cython, py/cext
"""

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class Recipe:
    """Definition of a project recipe."""

    name: str  # e.g., "cpp/executable"
    description: str
    category: str  # e.g., "cpp", "c", "py"
    variant: str  # e.g., "executable", "pybind11"
    build_system: str  # "cmake" or "skbuild"
    language: str  # "c", "cpp", "cython"
    framework: Optional[str] = None  # "pybind11", "nanobind", etc.
    configurable: bool = False
    config_template: Optional[str] = None
    default_options: dict[str, Any] = field(default_factory=dict)


# Recipe registry with category/variant naming
RECIPES: dict[str, Recipe] = {
    # C++ recipes
    "cpp/executable": Recipe(
        name="cpp/executable",
        description="C++ executable",
        category="cpp",
        variant="executable",
        build_system="cmake",
        language="cpp",
    ),
    "cpp/static": Recipe(
        name="cpp/static",
        description="C++ static library",
        category="cpp",
        variant="static",
        build_system="cmake",
        language="cpp",
    ),
    "cpp/shared": Recipe(
        name="cpp/shared",
        description="C++ shared library",
        category="cpp",
        variant="shared",
        build_system="cmake",
        language="cpp",
    ),
    "cpp/header-only": Recipe(
        name="cpp/header-only",
        description="C++ header-only library",
        category="cpp",
        variant="header-only",
        build_system="cmake",
        language="cpp",
    ),
    "cpp/library-with-tests": Recipe(
        name="cpp/library-with-tests",
        description="C++ library with tests",
        category="cpp",
        variant="library-with-tests",
        build_system="cmake",
        language="cpp",
    ),
    "cpp/app-with-lib": Recipe(
        name="cpp/app-with-lib",
        description="C++ app with internal library",
        category="cpp",
        variant="app-with-lib",
        build_system="cmake",
        language="cpp",
    ),
    "cpp/full": Recipe(
        name="cpp/full",
        description="C++ lib + app + tests",
        category="cpp",
        variant="full",
        build_system="cmake",
        language="cpp",
    ),
    # C recipes
    "c/executable": Recipe(
        name="c/executable",
        description="C executable",
        category="c",
        variant="executable",
        build_system="cmake",
        language="c",
    ),
    "c/static": Recipe(
        name="c/static",
        description="C static library",
        category="c",
        variant="static",
        build_system="cmake",
        language="c",
    ),
    "c/shared": Recipe(
        name="c/shared",
        description="C shared library",
        category="c",
        variant="shared",
        build_system="cmake",
        language="c",
    ),
    "c/header-only": Recipe(
        name="c/header-only",
        description="C header-only library",
        category="c",
        variant="header-only",
        build_system="cmake",
        language="c",
    ),
    "c/library-with-tests": Recipe(
        name="c/library-with-tests",
        description="C library with tests",
        category="c",
        variant="library-with-tests",
        build_system="cmake",
        language="c",
    ),
    "c/app-with-lib": Recipe(
        name="c/app-with-lib",
        description="C app with internal library",
        category="c",
        variant="app-with-lib",
        build_system="cmake",
        language="c",
    ),
    "c/full": Recipe(
        name="c/full",
        description="C lib + app + tests",
        category="c",
        variant="full",
        build_system="cmake",
        language="c",
    ),
    # Python extension recipes
    "py/pybind11": Recipe(
        name="py/pybind11",
        description="Python extension using pybind11",
        category="py",
        variant="pybind11",
        build_system="skbuild",
        language="cpp",
        framework="pybind11",
    ),
    "py/pybind11-flex": Recipe(
        name="py/pybind11-flex",
        description="Pybind11 extension with configurable native extras",
        category="py",
        variant="pybind11-flex",
        build_system="skbuild",
        language="cpp",
        framework="pybind11-flex",
        configurable=True,
        config_template="project.flex.json.mako",
        default_options={
            "env": "uv",
            "test_framework": "catch2",
            "build_examples": False,
        },
    ),
    "py/nanobind": Recipe(
        name="py/nanobind",
        description="Python extension using nanobind",
        category="py",
        variant="nanobind",
        build_system="skbuild",
        language="cpp",
        framework="nanobind",
    ),
    "py/cython": Recipe(
        name="py/cython",
        description="Python extension using Cython",
        category="py",
        variant="cython",
        build_system="skbuild",
        language="cython",
        framework="cython",
    ),
    "py/cext": Recipe(
        name="py/cext",
        description="Python C extension (Python.h)",
        category="py",
        variant="cext",
        build_system="skbuild",
        language="c",
        framework="c",
    ),
}

# Legacy type names mapped to new recipe names
LEGACY_TYPE_MAPPING: dict[str, str] = {
    # Old skbuild types -> py/* recipes
    "skbuild-pybind11": "py/pybind11",
    "skbuild-nanobind": "py/nanobind",
    "skbuild-cython": "py/cython",
    "skbuild-c": "py/cext",
    # Old flat types -> cpp/* recipes (default to C++)
    "executable": "cpp/executable",
    "static": "cpp/static",
    "shared": "cpp/shared",
    "header-only": "cpp/header-only",
    "library-with-tests": "cpp/library-with-tests",
    "app-with-lib": "cpp/app-with-lib",
    "full": "cpp/full",
}


def get_recipe(name: str) -> Recipe:
    """Get a recipe by name, supporting legacy names.

    Args:
        name: Recipe name (e.g., "cpp/executable") or legacy name (e.g., "executable")

    Returns:
        Recipe object

    Raises:
        ValueError: If recipe not found
    """
    # Check for legacy name first
    if name in LEGACY_TYPE_MAPPING:
        name = LEGACY_TYPE_MAPPING[name]

    if name not in RECIPES:
        raise ValueError(f"Unknown recipe: {name}")

    return RECIPES[name]


def get_recipes_by_category() -> dict[str, list[Recipe]]:
    """Get recipes grouped by category.

    Returns:
        Dict mapping category names to lists of recipes
    """
    categories: dict[str, list[Recipe]] = {}
    for recipe in RECIPES.values():
        if recipe.category not in categories:
            categories[recipe.category] = []
        categories[recipe.category].append(recipe)
    return categories


def list_recipes() -> list[str]:
    """Get list of all recipe names."""
    return list(RECIPES.keys())


def is_valid_recipe(name: str) -> bool:
    """Check if a recipe name is valid (including legacy names)."""
    return name in RECIPES or name in LEGACY_TYPE_MAPPING


def resolve_recipe_name(name: str) -> str:
    """Resolve a recipe name, converting legacy names to new format.

    Args:
        name: Recipe name or legacy type name

    Returns:
        Canonical recipe name (e.g., "cpp/executable")
    """
    if name in LEGACY_TYPE_MAPPING:
        return LEGACY_TYPE_MAPPING[name]
    return name
