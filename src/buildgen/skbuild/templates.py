"""Template loader for scikit-build-core project types.

Templates are stored as .mako files in the templates/ directory.
Supports override directories for customization.

Template paths use recipe naming: py/pybind11, py/cython, py/cext, py/nanobind
"""

from pathlib import Path
from typing import Optional

from mako.template import Template
from buildgen.templates.resolver import BUILTIN_TEMPLATES_DIR, TemplateResolver

# Path to templates directory (built-in)
TEMPLATES_DIR = BUILTIN_TEMPLATES_DIR

# Legacy skbuild type names (for backward compatibility)
# Maps legacy names to descriptions
SKBUILD_TYPES = {
    "skbuild-pybind11": "Python extension using pybind11 (C++ bindings)",
    "skbuild-pybind11-flex": "Pybind11 extension with configurable native extras",
    "skbuild-cython": "Python extension using Cython",
    "skbuild-c": "Python C extension (direct Python.h)",
    "skbuild-nanobind": "Python extension using nanobind (modern C++ bindings)",
}

# Map legacy type names to recipe template paths
LEGACY_TO_RECIPE_PATH = {
    "skbuild-pybind11": "py/pybind11",
    "skbuild-pybind11-flex": "py/pybind11-flex",
    "skbuild-cython": "py/cython",
    "skbuild-c": "py/cext",
    "skbuild-nanobind": "py/nanobind",
}

# Mapping of template type to output file structure
# Keys are output paths (with ${name} placeholder), values are template file paths
# Template paths are relative to the recipe directory (e.g., py/pybind11/)
TEMPLATE_FILES = {
    "skbuild-pybind11": {
        ".gitignore": "common/gitignore.python.mako",
        ".github/workflows/ci.yml": "common/github-workflows/ci.yml.mako",
        ".github/workflows/build-publish.yml": "common/github-workflows/build-publish.yml.mako",
        "CHANGELOG.md": "common/CHANGELOG.md.mako",
        "LICENSE": "common/LICENSE.mako",
        "Makefile": "common/Makefile.{env}.mako",
        "pyproject.toml": "pyproject.toml.mako",
        "README.md": "README.md.mako",
        "CMakeLists.txt": "CMakeLists.txt.mako",
        "src/${name}/__init__.py": "src/__init__.py.mako",
        "src/${name}/_core.cpp": "src/_core.cpp.mako",
        "src/${name}/py.typed": "src/py.typed.mako",
        "tests/test_${name}.py": "tests/test.py.mako",
    },
    "skbuild-pybind11-flex": {
        ".gitignore": "common/gitignore.python.mako",
        ".github/workflows/ci.yml": "common/github-workflows/ci.yml.mako",
        ".github/workflows/build-publish.yml": "common/github-workflows/build-publish.yml.mako",
        "CHANGELOG.md": "common/CHANGELOG.md.mako",
        "LICENSE": "common/LICENSE.mako",
        "Makefile": "common/Makefile.{env}.mako",
        "pyproject.toml": "pyproject.toml.mako",
        "README.md": "README.md.mako",
        "CMakeLists.txt": "CMakeLists.txt.mako",
        "project.flex.json": "project.flex.json.mako",
        "src/${name}/__init__.py": "src/__init__.py.mako",
        "src/${name}/_core.cpp": "src/_core.cpp.mako",
        "src/${name}/py.typed": "src/py.typed.mako",
        "examples/cli/main.cpp": "examples/cli/main.cpp.mako",
        "tests/test_${name}.py": "tests/test.py.mako",
        "tests/native/test_module.catch2.cpp": "tests/native/test_module.catch2.cpp.mako",
        "tests/native/test_module.gtest.cpp": "tests/native/test_module.gtest.cpp.mako",
    },
    "skbuild-cython": {
        ".gitignore": "common/gitignore.python.mako",
        ".github/workflows/ci.yml": "common/github-workflows/ci.yml.mako",
        ".github/workflows/build-publish.yml": "common/github-workflows/build-publish.yml.mako",
        "CHANGELOG.md": "common/CHANGELOG.md.mako",
        "LICENSE": "common/LICENSE.mako",
        "Makefile": "common/Makefile.{env}.mako",
        "pyproject.toml": "pyproject.toml.mako",
        "README.md": "README.md.mako",
        "CMakeLists.txt": "CMakeLists.txt.mako",
        "src/${name}/__init__.py": "src/__init__.py.mako",
        "src/${name}/_core.pyx": "src/_core.pyx.mako",
        "src/${name}/py.typed": "src/py.typed.mako",
        "tests/test_${name}.py": "tests/test.py.mako",
    },
    "skbuild-c": {
        ".gitignore": "common/gitignore.python.mako",
        ".github/workflows/ci.yml": "common/github-workflows/ci.yml.mako",
        ".github/workflows/build-publish.yml": "common/github-workflows/build-publish.yml.mako",
        "CHANGELOG.md": "common/CHANGELOG.md.mako",
        "LICENSE": "common/LICENSE.mako",
        "Makefile": "common/Makefile.{env}.mako",
        "pyproject.toml": "pyproject.toml.mako",
        "README.md": "README.md.mako",
        "CMakeLists.txt": "CMakeLists.txt.mako",
        "src/${name}/__init__.py": "src/__init__.py.mako",
        "src/${name}/_core.c": "src/_core.c.mako",
        "src/${name}/py.typed": "src/py.typed.mako",
        "tests/test_${name}.py": "tests/test.py.mako",
    },
    "skbuild-nanobind": {
        ".gitignore": "common/gitignore.python.mako",
        ".github/workflows/ci.yml": "common/github-workflows/ci.yml.mako",
        ".github/workflows/build-publish.yml": "common/github-workflows/build-publish.yml.mako",
        "CHANGELOG.md": "common/CHANGELOG.md.mako",
        "LICENSE": "common/LICENSE.mako",
        "Makefile": "common/Makefile.{env}.mako",
        "pyproject.toml": "pyproject.toml.mako",
        "README.md": "README.md.mako",
        "CMakeLists.txt": "CMakeLists.txt.mako",
        "src/${name}/__init__.py": "src/__init__.py.mako",
        "src/${name}/_core.cpp": "src/_core.cpp.mako",
        "src/${name}/py.typed": "src/py.typed.mako",
        "tests/test_${name}.py": "tests/test.py.mako",
    },
}


def get_recipe_path(template_type: str) -> str:
    """Get recipe path for a template type.

    Args:
        template_type: Legacy type (e.g., "skbuild-pybind11") or recipe path (e.g., "py/pybind11")

    Returns:
        Recipe path (e.g., "py/pybind11")
    """
    return LEGACY_TO_RECIPE_PATH.get(template_type, template_type)


def load_template(template_type: str, template_path: str) -> Template:
    """Load a Mako template from the templates directory.

    Args:
        template_type: Template type (e.g., "skbuild-pybind11")
        template_path: Relative path to template file within type directory

    Returns:
        Compiled Mako Template object.
    """
    full_path = TEMPLATES_DIR / template_type / template_path
    return Template(filename=str(full_path))


def render_template(template_type: str, template_path: str, **kwargs) -> str:
    """Load and render a Mako template.

    Args:
        template_type: Template type (e.g., "skbuild-pybind11")
        template_path: Relative path to template file within type directory
        **kwargs: Variables to pass to the template.

    Returns:
        Rendered template content.
    """
    template = load_template(template_type, template_path)
    return template.render(**kwargs)


def get_template_files(template_type: str, env_tool: str = "uv") -> dict[str, str]:
    """Get the template file mapping for a project type.

    Args:
        template_type: One of the SKBUILD_TYPES keys.
        env_tool: Environment tool ("uv" or "venv").

    Returns:
        Dict mapping output paths to template file paths.
    """
    if template_type not in TEMPLATE_FILES:
        raise ValueError(f"Unknown template type: {template_type}")

    files = {}
    for output_path, template_path in TEMPLATE_FILES[template_type].items():
        # Substitute {env} in template path for Makefile
        resolved_path = template_path.format(env=env_tool)
        files[output_path] = resolved_path

    return files


def resolve_template_files(
    template_type: str,
    env_tool: str = "uv",
    project_dir: Optional[Path] = None,
) -> dict[str, tuple[Path, str]]:
    """Get resolved template paths with override support.

    Checks for template overrides in this order:
    1. $BUILDGEN_TEMPLATES/{recipe_path}/
    2. {project_dir}/.buildgen/templates/{recipe_path}/
    3. ~/.buildgen/templates/{recipe_path}/
    4. Built-in templates

    Args:
        template_type: One of the SKBUILD_TYPES keys (e.g., "skbuild-pybind11").
        env_tool: Environment tool ("uv" or "venv").
        project_dir: Project directory for local overrides.

    Returns:
        Dict mapping output paths to (resolved_path, source) tuples.
        Source is one of: "env", "local", "global", "built-in"
    """
    if template_type not in TEMPLATE_FILES:
        raise ValueError(f"Unknown template type: {template_type}")

    # Get the recipe path (e.g., "py/pybind11" for "skbuild-pybind11")
    recipe_path = get_recipe_path(template_type)

    resolver = TemplateResolver(project_dir)
    results = {}

    for output_path, template_path in TEMPLATE_FILES[template_type].items():
        # Substitute {env} in template path for Makefile
        resolved_template = template_path.format(env=env_tool)

        # Check if this is a common template (e.g., Makefile)
        if resolved_template.startswith("common/"):
            filename = resolved_template.replace("common/", "")
            path, source = resolver.resolve_common(filename)
        else:
            # Use recipe path for template lookup
            path, source = resolver.resolve(recipe_path, resolved_template)

        results[output_path] = (path, source)

    return results
