"""Tests for the central version registry and its use by templates.

The registry only pays for itself if templates stop carrying literals, so the
drift guards below are the point of this module: they fail when a version is
written into a .mako file instead of read from buildgen.common.versions.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

from buildgen.common import versions

TEMPLATE_ROOT = Path(versions.__file__).resolve().parent.parent / "templates"
MAKO_FILES = sorted(TEMPLATE_ROOT.rglob("*.mako"))


def _templates_containing(needle: str) -> list[str]:
    return [
        str(p.relative_to(TEMPLATE_ROOT))
        for p in MAKO_FILES
        if needle in p.read_text(encoding="utf-8")
    ]


class TestRegistryShape:
    def test_dev_tools_are_all_in_pypi(self):
        assert set(versions.DEV_TOOLS) <= set(versions.PYPI)

    def test_build_backends_are_all_in_pypi(self):
        assert set(versions.PYPI) >= versions.BUILD_BACKENDS

    def test_capped_packages_are_all_in_pypi(self):
        assert set(versions.PYPI) >= versions.CAPPED_AT_NEXT_MINOR

    def test_requirement_names_are_all_in_pypi(self):
        assert set(versions.REQUIREMENT_NAMES) <= set(versions.PYPI)

    def test_templates_were_discovered(self):
        assert MAKO_FILES, "no .mako templates found; layout changed"


class TestOwnVersion:
    """The distribution version is declared twice; keep the two equal."""

    def test_dunder_version_matches_pyproject(self):
        """Read both from disk: an installed copy can lag the source mid-edit."""
        package_root = Path(versions.__file__).resolve().parent.parent
        init = (package_root / "__init__.py").read_text(encoding="utf-8")
        match = re.search(r'^__version__ = "([^"]+)"', init, re.MULTILINE)
        assert match, "no __version__ in buildgen/__init__.py"

        data = tomllib.loads(
            (package_root.parents[1] / "pyproject.toml").read_text(encoding="utf-8")
        )
        assert match.group(1) == data["project"]["version"]


class TestOwnDevGroup:
    """buildgen's own dev floors are a second copy; keep them equal."""

    def _own_dev_group(self) -> dict[str, str]:
        root = Path(versions.__file__).resolve().parents[3]
        data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        floors = {}
        for spec in data["dependency-groups"]["dev"]:
            name, _, floor = spec.partition(">=")
            floors[name] = floor
        return floors

    @pytest.mark.parametrize("tool", versions.DEV_TOOLS)
    def test_floor_matches_the_registry(self, tool):
        assert self._own_dev_group()[tool] == versions.PYPI[tool]


class TestNextMinor:
    @pytest.mark.parametrize(
        ("version", "expected"),
        [("0.12.6", "0.13"), ("0.12", "0.13"), ("1.9.0", "1.10"), ("2.0.0", "2.1")],
    )
    def test_increments_minor_and_drops_patch(self, version, expected):
        assert versions.next_minor(version) == expected

    def test_rejects_version_without_minor(self):
        with pytest.raises(ValueError, match="no minor component"):
            versions.next_minor("1")


class TestRequirement:
    def test_plain_package_gets_a_floor_only(self):
        assert versions.requirement("ruff") == f"ruff>={versions.PYPI['ruff']}"

    def test_uv_build_is_capped_at_the_next_minor(self):
        assert versions.requirement("uv-build") == "uv_build>=0.12.6,<0.13"

    def test_cap_tracks_the_resolved_version(self):
        """A PyPI-resolved uv-build must move its own upper bound with it."""
        assert (
            versions.requirement("uv-build", {"uv-build": "0.13.2"})
            == "uv_build>=0.13.2,<0.14"
        )

    def test_override_table_wins_over_the_registry(self):
        assert versions.requirement("ruff", {"ruff": "99.0.0"}) == "ruff>=99.0.0"

    def test_falls_back_to_the_registry_for_missing_keys(self):
        assert (
            versions.requirement("ruff", {"mypy": "1.0.0"})
            == f"ruff>={versions.PYPI['ruff']}"
        )

    def test_unknown_package_gets_a_zero_floor(self):
        assert versions.requirement("nonexistent-pkg") == "nonexistent-pkg>=0"


class TestAction:
    def test_returns_owner_repo_at_ref(self):
        assert (
            versions.action("actions/checkout")
            == f"actions/checkout@{versions.ACTIONS['actions/checkout']}"
        )

    def test_unknown_action_raises(self):
        with pytest.raises(KeyError):
            versions.action("nobody/nothing")


class TestNoDriftFromTheRegistry:
    """Every literal below belongs in versions.py, not in a template."""

    @pytest.mark.parametrize(
        "version", [v for v in versions.PYPI.values() if v.count(".") >= 2]
    )
    def test_no_pypi_version_literal(self, version):
        assert not _templates_containing(version)

    @pytest.mark.parametrize("tag", sorted(versions.GIT_TAGS.values()))
    def test_no_git_tag_literal(self, tag):
        assert not _templates_containing(f"GIT_TAG {tag}")

    @pytest.mark.parametrize("floor", ["min", "python_ext_min", "flex_min"])
    def test_no_cmake_range_literal(self, floor):
        needle = f"{versions.CMAKE[floor]}...{versions.CMAKE['policy_max']}"
        assert not _templates_containing(needle)

    def test_no_literal_action_ref(self):
        uses = re.compile(r"uses:\s*[\w.-]+/[\w.-]+@")
        offenders = [
            str(p.relative_to(TEMPLATE_ROOT))
            for p in MAKO_FILES
            if uses.search(p.read_text(encoding="utf-8"))
        ]
        assert not offenders, f"templates pinning actions directly: {offenders}"


class TestGeneratedOutput:
    def _nodeps_pyproject(self, tmp_path: Path) -> str:
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        gen = SkbuildProjectGenerator(
            "purepkg", "py/nodeps", tmp_path / "purepkg", update_deps=False
        )
        gen.generate()
        return (tmp_path / "purepkg" / "pyproject.toml").read_text()

    def test_pure_python_uses_the_capped_uv_build_pin(self, tmp_path):
        data = tomllib.loads(self._nodeps_pyproject(tmp_path))
        assert data["build-system"]["build-backend"] == "uv_build"
        assert data["build-system"]["requires"] == [versions.requirement("uv-build")]

    def test_pure_python_declares_the_src_layout(self, tmp_path):
        data = tomllib.loads(self._nodeps_pyproject(tmp_path))
        backend = data["tool"]["uv"]["build-backend"]
        assert backend["module-name"] == "purepkg"
        assert backend["module-root"] == "src"
        # uv_build ships only the module by default; these are the files the
        # hatchling sdist `include` list used to carry.
        assert set(backend["source-include"]) == {
            "tests/**",
            "CHANGELOG.md",
            "LICENSE",
        }

    def test_dev_group_comes_from_the_registry(self, tmp_path):
        data = tomllib.loads(self._nodeps_pyproject(tmp_path))
        assert data["dependency-groups"]["dev"] == [
            versions.requirement(tool) for tool in versions.DEV_TOOLS
        ]

    def test_generated_workflow_uses_registry_action_refs(self, tmp_path):
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        gen = SkbuildProjectGenerator(
            "purepkg", "py/nodeps", tmp_path / "purepkg", update_deps=False
        )
        gen.generate()
        ci = (tmp_path / "purepkg" / ".github/workflows/ci.yml").read_text()
        assert versions.action("actions/checkout") in ci
        assert versions.action("astral-sh/setup-uv") in ci
