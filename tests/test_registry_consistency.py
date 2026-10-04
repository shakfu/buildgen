"""Cross-registry consistency checks.

A recipe is described in three places that are kept in sync by hand:

- `buildgen.recipes.RECIPES` -- the user-visible catalogue,
- `CMakeProjectGenerator.TEMPLATE_FILES` -- file maps for CMake recipes,
- `buildgen.skbuild.templates.TEMPLATE_FILES` -- file maps for Python recipes,
- `QuartoProjectGenerator.TEMPLATE_FILES` -- file maps for Quarto recipes.

Adding an entry to one and forgetting the others used to fail only at runtime,
when a user ran the recipe. These tests turn that into a test failure.
"""

from __future__ import annotations

import pytest

from buildgen.cmake.project_generator import CMakeProjectGenerator, is_cmake_recipe
from buildgen.quarto.generator import QuartoProjectGenerator
from buildgen.recipes import (
    LEGACY_TYPE_MAPPING,
    RECIPES,
    get_recipe,
    resolve_recipe_name,
)
from buildgen.skbuild.templates import (
    LEGACY_TO_RECIPE_PATH,
    PY_PLAIN_TYPES,
    SKBUILD_TYPES,
    TEMPLATE_FILES,
    get_registry_key,
)
from buildgen.templates.resolver import BUILTIN_TEMPLATES_DIR

KNOWN_BUILD_SYSTEMS = {"cmake", "skbuild", "python", "quarto"}


class TestRecipeRegistry:
    """Invariants of the recipe catalogue itself."""

    def test_every_recipe_has_a_known_build_system(self):
        for name, recipe in RECIPES.items():
            assert recipe.build_system in KNOWN_BUILD_SYSTEMS, (
                f"{name} has unknown build system {recipe.build_system!r}"
            )

    def test_recipe_keys_match_their_name_field(self):
        for name, recipe in RECIPES.items():
            assert recipe.name == name
            assert name == f"{recipe.category}/{recipe.variant}"

    def test_legacy_names_resolve_to_registered_recipes(self):
        for legacy, canonical in LEGACY_TYPE_MAPPING.items():
            assert canonical in RECIPES, f"{legacy} maps to unknown {canonical}"
            assert get_recipe(legacy) is RECIPES[canonical]


class TestCMakeRegistrySync:
    """RECIPES <-> CMakeProjectGenerator.TEMPLATE_FILES."""

    @pytest.mark.parametrize(
        "recipe_name",
        sorted(n for n, r in RECIPES.items() if r.build_system == "cmake"),
    )
    def test_cmake_recipe_has_templates(self, recipe_name):
        assert recipe_name in CMakeProjectGenerator.TEMPLATE_FILES

    @pytest.mark.parametrize(
        "recipe_name", sorted(CMakeProjectGenerator.TEMPLATE_FILES)
    )
    def test_cmake_template_set_has_a_recipe(self, recipe_name):
        assert recipe_name in RECIPES
        assert RECIPES[recipe_name].build_system == "cmake"

    def test_is_cmake_recipe_matches_the_registry(self):
        for name, recipe in RECIPES.items():
            assert is_cmake_recipe(name) is (recipe.build_system == "cmake")
        for legacy, canonical in LEGACY_TYPE_MAPPING.items():
            expected = RECIPES[canonical].build_system == "cmake"
            assert is_cmake_recipe(legacy) is expected

    def test_is_cmake_recipe_rejects_unknown_names(self):
        assert not is_cmake_recipe("cpp/does-not-exist")
        assert not is_cmake_recipe("")


class TestQuartoRegistrySync:
    """RECIPES <-> QuartoProjectGenerator.TEMPLATE_FILES / OUTPUT_DIRS."""

    def test_template_sets_match_the_registry(self):
        quarto = {n for n, r in RECIPES.items() if r.build_system == "quarto"}
        assert set(QuartoProjectGenerator.TEMPLATE_FILES) == quarto

    def test_every_template_set_declares_where_output_goes(self):
        """Projects have an output dir; single files list their outputs."""
        dirs = set(QuartoProjectGenerator.OUTPUT_DIRS)
        files = set(QuartoProjectGenerator.OUTPUTS)
        assert not dirs & files
        assert dirs | files == set(QuartoProjectGenerator.TEMPLATE_FILES)


class TestPythonRegistrySync:
    """RECIPES <-> buildgen.skbuild.templates.TEMPLATE_FILES."""

    @pytest.mark.parametrize(
        "recipe_name",
        sorted(
            n for n, r in RECIPES.items() if r.build_system in ("skbuild", "python")
        ),
    )
    def test_python_recipe_has_templates(self, recipe_name):
        assert RECIPES[recipe_name].template_type in TEMPLATE_FILES

    @pytest.mark.parametrize("template_type", sorted(TEMPLATE_FILES))
    def test_python_template_set_has_a_recipe(self, template_type):
        recipes = [
            r
            for r in RECIPES.values()
            if r.build_system in ("skbuild", "python")
            and r.template_type == template_type
        ]
        assert len(recipes) == 1, (
            f"{template_type} is claimed by {len(recipes)} recipes"
        )

    @pytest.mark.parametrize("template_type", sorted(TEMPLATE_FILES))
    def test_registry_key_round_trips(self, template_type):
        """Both the legacy name and the recipe path resolve to the same key."""
        from buildgen.skbuild.templates import get_recipe_path

        assert get_registry_key(template_type) == template_type
        assert get_registry_key(get_recipe_path(template_type)) == template_type

    def test_legacy_template_names_agree_across_modules(self):
        """recipes.LEGACY_TYPE_MAPPING and templates.LEGACY_TO_RECIPE_PATH agree."""
        for legacy, recipe_path in LEGACY_TO_RECIPE_PATH.items():
            assert recipe_path in RECIPES, f"{legacy} maps to unknown {recipe_path}"
            if legacy in LEGACY_TYPE_MAPPING:
                assert LEGACY_TYPE_MAPPING[legacy] == recipe_path

    def test_type_descriptions_cover_every_template_set(self):
        assert set(TEMPLATE_FILES) == set(SKBUILD_TYPES) | set(PY_PLAIN_TYPES)


class TestTemplateFilesExist:
    """Every referenced built-in template file is actually present on disk."""

    @staticmethod
    def _resolve(template_type: str, template_path: str):
        from buildgen.skbuild.templates import get_recipe_path

        if template_path.startswith("common/"):
            return BUILTIN_TEMPLATES_DIR / template_path
        return BUILTIN_TEMPLATES_DIR / get_recipe_path(template_type) / template_path

    @pytest.mark.parametrize("template_type", sorted(TEMPLATE_FILES))
    def test_python_templates_exist(self, template_type):
        for template_path in TEMPLATE_FILES[template_type].values():
            for env in ("uv", "venv"):
                path = self._resolve(template_type, template_path.format(env=env))
                assert path.is_file(), f"{template_type}: missing {path}"

    @pytest.mark.parametrize(
        ("generator", "recipe_name"),
        [
            (CMakeProjectGenerator, n)
            for n in sorted(CMakeProjectGenerator.TEMPLATE_FILES)
        ]
        + [
            (QuartoProjectGenerator, n)
            for n in sorted(QuartoProjectGenerator.TEMPLATE_FILES)
        ],
    )
    def test_template_map_files_exist(self, generator, recipe_name):
        for template_path in generator.TEMPLATE_FILES[recipe_name].values():
            if template_path.startswith("common/"):
                path = BUILTIN_TEMPLATES_DIR / template_path
            else:
                path = BUILTIN_TEMPLATES_DIR / recipe_name / template_path
            assert path.is_file(), f"{recipe_name}: missing {path}"

    def test_configurable_recipes_have_their_config_template(self):
        for name, recipe in RECIPES.items():
            if not recipe.configurable:
                continue
            assert recipe.config_template, f"{name} is configurable without a template"
            path = (
                BUILTIN_TEMPLATES_DIR
                / resolve_recipe_name(name)
                / recipe.config_template
            )
            assert path.is_file(), f"{name}: missing {path}"
