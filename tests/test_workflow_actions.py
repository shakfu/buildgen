"""Tests for scripts/update_workflow_actions.py and the pins it maintains.

The updater used to normalize every action ref to a bare major tag (``@v10``).
Not every action publishes one -- ``astral-sh/setup-uv`` stopped after v7 --
and a workflow pinned to a nonexistent tag fails at action-resolution time,
taking every job in the file down before a single step runs. These tests keep
the fallback honest without touching the network.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "update_workflow_actions.py"


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "update_workflow_actions", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec: @dataclass resolves annotations via sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


uwa = _load_script()


class FakeResolver(uwa.Resolver):
    """Resolver backed by an in-memory registry of {action: (latest, tags)}."""

    def __init__(self, registry: dict[str, tuple[str | None, set[str]]]) -> None:
        super().__init__(use_gh=False)
        self._registry = registry
        self._fetch = lambda action: self._registry.get(action, (None, set()))[0]
        self._exists = lambda action, tag: (
            tag in self._registry.get(action, (None, set()))[1]
        )


@pytest.mark.parametrize(
    ("tag", "style", "expected"),
    [
        ("v8.2.0", "major", ["v8", "v8.2", "v8.2.0"]),
        ("v10.0.1", "major", ["v10", "v10.0", "v10.0.1"]),
        ("v4", "major", ["v4"]),
        ("8.2.0", "major", ["v8", "v8.2", "v8.2.0", "8.2.0"]),
        ("v8.2.0", "full", ["v8.2.0"]),
        ("v1.0.0-rc1", "major", ["v1.0.0-rc1"]),
    ],
)
def test_ref_candidates(tag, style, expected):
    assert uwa.ref_candidates(tag, style) == expected


def test_desired_ref_prefers_floating_major_when_published():
    resolver = FakeResolver({"actions/checkout": ("v7.0.1", {"v7", "v7.0", "v7.0.1"})})
    assert resolver.desired_ref("actions/checkout", "major") == "v7"


def test_desired_ref_falls_back_to_minor_when_major_tag_absent():
    """pypa/cibuildwheel publishes v4.2 but no bare v4."""
    resolver = FakeResolver({"pypa/cibuildwheel": ("v4.2.0", {"v4.2", "v4.2.0"})})
    assert resolver.desired_ref("pypa/cibuildwheel", "major") == "v4.2"


def test_desired_ref_falls_back_to_full_tag_when_no_floating_tags():
    """astral-sh/setup-uv dropped floating tags after v7 -- the CI failure."""
    resolver = FakeResolver({"astral-sh/setup-uv": ("v10.0.1", {"v10.0.1"})})
    assert resolver.desired_ref("astral-sh/setup-uv", "major") == "v10.0.1"


def test_desired_ref_is_none_when_no_candidate_exists():
    resolver = FakeResolver({"some/action": ("v3.1.0", set())})
    assert resolver.desired_ref("some/action", "major") is None


def test_desired_ref_is_none_when_latest_release_unknown():
    resolver = FakeResolver({"some/action": (None, {"v1"})})
    assert resolver.desired_ref("some/action", "major") is None


def test_apply_changes_leaves_pins_alone_when_ref_unresolvable(tmp_path):
    """An unresolvable action must keep its working pin, not lose it."""
    workflow = tmp_path / "ci.yml"
    workflow.write_text("    - uses: some/action@v3\n", encoding="utf-8")
    resolver = FakeResolver({"some/action": ("v9.0.0", set())})

    assert uwa.apply_changes([workflow], resolver, "major") == 0
    assert workflow.read_text(encoding="utf-8") == "    - uses: some/action@v3\n"


def test_apply_changes_leaves_branch_refs_alone(tmp_path):
    workflow = tmp_path / "ci.yml"
    workflow.write_text(
        "    - uses: pypa/gh-action-pypi-publish@release/v1\n", encoding="utf-8"
    )
    resolver = FakeResolver(
        {"pypa/gh-action-pypi-publish": ("v1.14.2", {"v1", "v1.14"})}
    )

    assert uwa.apply_changes([workflow], resolver, "major") == 0
    assert "release/v1" in workflow.read_text(encoding="utf-8")


def test_apply_changes_rewrites_to_the_existing_ref(tmp_path):
    workflow = tmp_path / "ci.yml"
    workflow.write_text("        uses: astral-sh/setup-uv@v6\n", encoding="utf-8")
    resolver = FakeResolver({"astral-sh/setup-uv": ("v10.0.1", {"v10.0.1"})})

    assert uwa.apply_changes([workflow], resolver, "major") == 1
    assert (
        workflow.read_text(encoding="utf-8")
        == "        uses: astral-sh/setup-uv@v10.0.1\n"
    )


def _pinned_refs() -> dict[str, set[str]]:
    """Map every action referenced in this repo to the refs it is pinned at.

    Covers both pin shapes: `uses:` lines in this repo's own workflows and
    entries in the ACTIONS registry the generated workflows render from.
    """
    refs: dict[str, set[str]] = {}
    for pattern in uwa.SCAN_GLOBS:
        for path in REPO_ROOT.glob(pattern):
            if not path.is_file():
                continue
            for m in uwa.pin_re(path).finditer(path.read_text(encoding="utf-8")):
                refs.setdefault(m.group("action"), set()).add(m.group("ref"))
    return refs


def test_workflow_files_were_discovered():
    assert _pinned_refs(), "no action refs found; SCAN_GLOBS or layout changed"


def test_registry_covers_every_ref_this_repo_pins():
    """Own workflows and the registry must agree, so one bump moves both."""
    from buildgen.common.versions import ACTIONS

    missing = sorted(set(_pinned_refs()) - set(ACTIONS))
    assert not missing, f"actions pinned outside versions.ACTIONS: {missing}"


def test_apply_changes_rewrites_the_registry_table(tmp_path):
    """A registry entry is rewritten in place, key and quoting intact."""
    registry = tmp_path / "versions.py"
    registry.write_text(
        'ACTIONS = {\n    "actions/checkout": "v6",\n}\n', encoding="utf-8"
    )
    resolver = FakeResolver({"actions/checkout": ("v7.0.1", {"v7", "v7.0.1"})})

    assert uwa.apply_changes([registry], resolver, "major") == 1
    assert registry.read_text(encoding="utf-8") == (
        'ACTIONS = {\n    "actions/checkout": "v7",\n}\n'
    )


def test_every_action_is_pinned_consistently():
    """One ref per action across workflows and templates, so bumps stay uniform."""
    inconsistent = {a: sorted(r) for a, r in _pinned_refs().items() if len(r) > 1}
    assert not inconsistent, f"actions pinned at differing refs: {inconsistent}"


def test_no_bare_major_pin_for_actions_without_floating_tags():
    """Guards the exact regression: these publish no moving major tag."""
    no_floating_major = {"astral-sh/setup-uv", "pypa/cibuildwheel"}
    for action, refs in _pinned_refs().items():
        if action not in no_floating_major:
            continue
        for ref in refs:
            assert not re.fullmatch(r"v?\d+", ref), (
                f"{action}@{ref} is a bare major tag, which {action} does not "
                "publish; the workflow will fail to resolve"
            )
