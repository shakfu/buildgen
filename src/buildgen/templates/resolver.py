"""Template resolver with override support.

Resolves template paths with a four-tier hierarchy:
1. Environment variable: $BUILDGEN_TEMPLATES/
2. Project-local: .buildgen/templates/
3. User-global: ~/.buildgen/templates/
4. Built-in: src/buildgen/templates/
"""

import os
import shutil
from pathlib import Path
from typing import Optional

# Built-in templates directory
BUILTIN_TEMPLATES_DIR = Path(__file__).parent


class TemplateResolver:
    """Resolve template paths with override support.

    Templates are resolved by checking multiple directories in order,
    returning the first match found. This allows users to override
    specific template files while falling back to built-in defaults.

    Search order:
    1. $BUILDGEN_TEMPLATES (if set)
    2. {project_dir}/.buildgen/templates (if project_dir provided)
    3. ~/.buildgen/templates
    4. Built-in templates

    Example:
        resolver = TemplateResolver(project_dir=Path.cwd())
        path, source = resolver.resolve("skbuild-pybind11", "pyproject.toml.mako")
    """

    def __init__(self, project_dir: Optional[Path] = None):
        """Initialize the resolver.

        Args:
            project_dir: Project directory for local overrides. If None,
                         local override directory is skipped.
        """
        env_templates = os.environ.get("BUILDGEN_TEMPLATES")

        self.search_paths: list[tuple[str, Optional[Path]]] = [
            ("env", Path(env_templates) if env_templates else None),
            ("local", project_dir / ".buildgen/templates" if project_dir else None),
            ("global", Path.home() / ".buildgen/templates"),
            ("built-in", BUILTIN_TEMPLATES_DIR),
        ]

    def resolve(self, template_type: str, filename: str) -> tuple[Path, str]:
        """Find a template file, checking override directories first.

        Args:
            template_type: Template type (e.g., "skbuild-pybind11")
            filename: Template filename (e.g., "pyproject.toml.mako")

        Returns:
            Tuple of (resolved path, source label)

        Raises:
            FileNotFoundError: If template not found in any search path
        """
        for source, search_path in self.search_paths:
            if search_path is None:
                continue
            candidate = search_path / template_type / filename
            if candidate.exists():
                return candidate, source

        raise FileNotFoundError(f"Template not found: {template_type}/{filename}")

    def resolve_common(self, filename: str) -> tuple[Path, str]:
        """Find a common template file (shared across types).

        Args:
            filename: Template filename (e.g., "Makefile.uv.mako")

        Returns:
            Tuple of (resolved path, source label)

        Raises:
            FileNotFoundError: If template not found in any search path
        """
        for source, search_path in self.search_paths:
            if search_path is None:
                continue
            candidate = search_path / "common" / filename
            if candidate.exists():
                return candidate, source

        raise FileNotFoundError(f"Common template not found: common/{filename}")

    def list_overrides(self, template_type: str) -> dict[str, str]:
        """List which files have overrides and from where.

        Returns:
            Dict mapping filename to source label for files with overrides
        """
        overrides = {}

        for source, search_path in self.search_paths:
            if search_path is None or source == "built-in":
                continue
            override_dir = search_path / template_type
            if override_dir.exists():
                for f in override_dir.rglob("*.mako"):
                    rel_path = str(f.relative_to(override_dir))
                    if rel_path not in overrides:
                        overrides[rel_path] = source

        return overrides


def get_builtin_template_recipes() -> list[str]:
    """Get available built-in template recipes.

    Returns:
        List of recipe paths (e.g., ["py/pybind11", "py/cython", ...])
    """
    recipes = []
    for category_dir in BUILTIN_TEMPLATES_DIR.iterdir():
        if not category_dir.is_dir():
            continue
        if category_dir.name in (
            "common",
            "__pycache__",
        ) or category_dir.name.startswith("_"):
            continue
        # Look for variant directories within category
        for variant_dir in category_dir.iterdir():
            if variant_dir.is_dir() and not variant_dir.name.startswith("_"):
                recipes.append(f"{category_dir.name}/{variant_dir.name}")
    return sorted(recipes)


def get_builtin_template_types() -> list[str]:
    """Get available built-in template types (legacy).

    Returns:
        List of recipe paths (same as get_builtin_template_recipes)
    """
    return get_builtin_template_recipes()


def copy_templates(
    recipe_path: str,
    dest_dir: Path,
    include_common: bool = True,
) -> list[Path]:
    """Copy built-in templates to a destination directory.

    Args:
        recipe_path: Recipe path to copy (e.g., "py/pybind11")
        dest_dir: Destination directory (e.g., .buildgen/templates or ~/.buildgen/templates)
        include_common: Whether to include common templates

    Returns:
        List of copied file paths
    """
    src_dir = BUILTIN_TEMPLATES_DIR / recipe_path
    if not src_dir.exists():
        raise ValueError(f"Recipe template not found: {recipe_path}")

    dest_type_dir = dest_dir / recipe_path
    dest_type_dir.mkdir(parents=True, exist_ok=True)

    copied = []

    # Copy recipe-specific templates
    for src_file in src_dir.rglob("*.mako"):
        rel_path = src_file.relative_to(src_dir)
        dest_file = dest_type_dir / rel_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)
        copied.append(dest_file)

    # Copy common templates if requested
    if include_common:
        common_src = BUILTIN_TEMPLATES_DIR / "common"
        if common_src.exists():
            common_dest = dest_dir / "common"
            common_dest.mkdir(parents=True, exist_ok=True)
            for src_file in common_src.rglob("*.mako"):
                rel_path = src_file.relative_to(common_src)
                dest_file = common_dest / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest_file)
                copied.append(dest_file)

    return copied
