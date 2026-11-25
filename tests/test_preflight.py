"""Tests for the doctor preflight and install suggestions."""

from __future__ import annotations

import json
from argparse import Namespace

import pytest

from buildgen.cli.commands import cmd_doctor, cmd_new, cmd_test
from buildgen.common import toolchain
from buildgen.common.toolchain import ToolInfo, diagnostics_json, install_hint


def _without(monkeypatch: pytest.MonkeyPatch, *missing: str) -> None:
    tools = {
        name: ToolInfo(name, None if name in missing else f"/bin/{name}", None)
        for name in toolchain.INSTALL_HINTS
    }
    monkeypatch.setattr(toolchain, "discover_tools", lambda: tools)


def _new_args(tmp_path, **kw) -> Namespace:
    base = {
        "name": "proj",
        "recipe": "cpp/executable",
        "output": str(tmp_path / "proj"),
        "env": None,
        "dry_run": False,
        "force": False,
        "skip_doctor": False,
    }
    return Namespace(**{**base, **kw})


@pytest.mark.parametrize("key", ["darwin", "apt", "dnf", "pacman", "winget"])
def test_every_tool_has_a_hint_per_platform(key):
    for tool in toolchain.INSTALL_HINTS:
        assert install_hint(tool, key)


def test_install_hint_unknown_platform_returns_none():
    assert install_hint("cmake", "plan9") is None


def test_install_platform_does_not_run_anything(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("install suggestion must not execute commands")

    monkeypatch.setattr(toolchain.subprocess, "run", boom)
    monkeypatch.setattr(toolchain.sys, "platform", "darwin")
    assert install_hint("cmake") == "brew install cmake"


def test_new_fails_before_writing_when_tool_missing(tmp_path, monkeypatch, capsys):
    _without(monkeypatch, "cxx")
    monkeypatch.setattr(toolchain.sys, "platform", "darwin")
    with pytest.raises(SystemExit) as exc:
        cmd_new(_new_args(tmp_path))
    assert exc.value.code == 1
    assert not (tmp_path / "proj").exists()
    err = capsys.readouterr().err
    assert "cxx" in err
    assert "xcode-select --install" in err


def test_new_skip_doctor_generates_anyway(tmp_path, monkeypatch):
    _without(monkeypatch, "cxx", "cmake")
    cmd_new(_new_args(tmp_path, skip_doctor=True))
    assert (tmp_path / "proj").exists()


def test_test_build_checks_all_recipes_first(tmp_path, monkeypatch, capsys):
    _without(monkeypatch, "quarto")
    args = Namespace(
        build=True,
        test=False,
        all=False,
        name=None,
        category="quarto",
        output=str(tmp_path / "out"),
        keep=False,
        skip_doctor=False,
    )
    with pytest.raises(SystemExit):
        cmd_test(args)
    assert not (tmp_path / "out").exists()
    assert "quarto" in capsys.readouterr().err


def test_doctor_prints_hint_for_missing_tool(monkeypatch, capsys):
    _without(monkeypatch, "cmake")
    monkeypatch.setattr(toolchain.sys, "platform", "darwin")
    with pytest.raises(SystemExit):
        cmd_doctor(Namespace(json=False, recipe="cpp/executable"))
    out = capsys.readouterr()
    assert "install: brew install cmake" in out.out
    assert "cmake: brew install cmake" in out.err


def test_diagnostics_json_includes_install_only_when_missing(monkeypatch):
    monkeypatch.setattr(toolchain.sys, "platform", "darwin")
    data = json.loads(
        diagnostics_json(
            {
                "cmake": ToolInfo("cmake", None, None),
                "make": ToolInfo("make", "/bin/make", "4"),
            }
        )
    )
    assert data["tools"]["cmake"]["install"] == "brew install cmake"
    assert data["tools"]["make"]["install"] is None
