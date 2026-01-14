"""End-to-end recipe generation checks."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Callable

import pytest

from buildgen.cmake.project_generator import CMakeProjectGenerator
from buildgen.recipes import RECIPES, Recipe
from buildgen.skbuild.generator import SkbuildProjectGenerator

CMAKE_AVAILABLE = shutil.which("cmake") is not None

COMPILABLE_RECIPES = sorted(
    name for name, recipe in RECIPES.items() if recipe.build_system == "cmake"
)
SKBUILD_RECIPES = sorted(
    name for name, recipe in RECIPES.items() if recipe.build_system == "skbuild"
)
SKBUILD_TEST_CONTEXT_OVERRIDES: dict[str, dict] = {
    "py/pybind11-flex": {"options": {"test_framework": "none", "build_examples": False}}
}


def _sanitized_project_name(recipe_name: str) -> str:
    """Convert recipe name (e.g., cpp/executable) into a safe project name."""
    sanitized = recipe_name.replace("/", "_").replace("-", "_")
    if sanitized[0].isdigit():
        sanitized = f"proj_{sanitized}"
    return sanitized


def _generate_project(
    recipe_name: str, dir_factory: Callable[[str], Path]
) -> tuple[Recipe, Path]:
    """Generate a project for the given recipe inside the persistent build dir."""
    recipe = RECIPES[recipe_name]
    project_name = _sanitized_project_name(recipe_name)
    output_dir = dir_factory(project_name)

    if recipe.build_system == "cmake":
        generator = CMakeProjectGenerator(project_name, recipe_name, output_dir)
    elif recipe.build_system == "skbuild":
        skbuild_type = f"skbuild-{recipe.framework}"
        env_tool = recipe.default_options.get("env", "uv")
        context = {}
        if recipe.default_options:
            context["options"] = dict(recipe.default_options)
        override = SKBUILD_TEST_CONTEXT_OVERRIDES.get(recipe_name)
        if override:
            context.setdefault("options", {})
            if "options" in override:
                context["options"].update(override["options"])
            for key, value in override.items():
                if key == "options":
                    continue
                context[key] = value
        generator = SkbuildProjectGenerator(
            project_name,
            skbuild_type,
            output_dir,
            env_tool=env_tool,
            context=context or None,
        )
    else:
        raise AssertionError(f"Unsupported build system {recipe.build_system}")

    created = generator.generate()
    assert created, f"{recipe_name} generation produced no files"
    return recipe, output_dir


def _configure_and_build(project_dir: Path) -> None:
    """Configure the generated project with CMake and build it."""
    if not CMAKE_AVAILABLE:
        pytest.skip("cmake is not available on PATH")

    build_dir = project_dir / "build"
    configure = subprocess.run(
        ["cmake", "-S", str(project_dir), "-B", str(build_dir)],
        check=False,
        capture_output=True,
        text=True,
    )
    if configure.returncode != 0:
        stdout = configure.stdout.strip()
        stderr = configure.stderr.strip()
        pytest.fail(
            f"CMake configure failed for {project_dir}:\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        )

    build = subprocess.run(
        ["cmake", "--build", str(build_dir)],
        check=False,
        capture_output=True,
        text=True,
    )
    if build.returncode != 0:
        stdout = build.stdout.strip()
        stderr = build.stderr.strip()
        pytest.fail(
            f"CMake build failed for {project_dir}:\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        )


def _run_command(cmd: list[str], cwd: Path, label: str) -> None:
    """Run a command and fail the test if it exits non-zero."""
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        pytest.fail(
            f"{label} failed for {cwd}:\nCommand: {' '.join(cmd)}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        )


def _build_skbuild_project(project_dir: Path) -> None:
    """Run uv sync and python -m build for a skbuild project."""
    _run_command(["uv", "sync"], cwd=project_dir, label="uv sync")
    _run_command(["uv", "build"], cwd=project_dir, label="uv build")


@pytest.mark.parametrize("recipe_name", sorted(RECIPES.keys()))
def test_recipe_generates(build_project_dir_factory, recipe_name):
    """Every recipe should render its template set without errors."""
    recipe, project_dir = _generate_project(recipe_name, build_project_dir_factory)

    if recipe.build_system == "cmake":
        assert (project_dir / "CMakeLists.txt").exists()
        assert (project_dir / "Makefile").exists()
    else:
        assert (project_dir / "pyproject.toml").exists()
        assert (project_dir / "CMakeLists.txt").exists()


@pytest.mark.parametrize("recipe_name", COMPILABLE_RECIPES)
def test_cmake_recipes_compile(build_project_dir_factory, recipe_name):
    """CMake-based recipes should configure and compile cleanly."""
    _, project_dir = _generate_project(recipe_name, build_project_dir_factory)
    _configure_and_build(project_dir)


@pytest.mark.parametrize("recipe_name", SKBUILD_RECIPES)
def test_skbuild_recipes_build(
    build_project_dir_factory, recipe_name, build_skbuild_enabled
):
    """Optionally run uv sync + python -m build for skbuild recipes."""
    if not build_skbuild_enabled:
        pytest.skip("Disabled via --skip-skbuild-build")

    _, project_dir = _generate_project(recipe_name, build_project_dir_factory)
    _build_skbuild_project(project_dir)
