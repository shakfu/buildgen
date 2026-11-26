"""py/maturin and py/maturin-flex: option resolution, rendered files, builds."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import pytest

from buildgen.cli import cmd_new, cmd_render
from buildgen.recipes import RECIPES
from buildgen.skbuild.generator import SkbuildProjectGenerator
from buildgen.skbuild.maturin import resolve

CARGO_AVAILABLE = shutil.which("cargo") is not None
FLEX = RECIPES["py/maturin-flex"]

# (bindings, abi3, rust_tests) -> expected wheel tag fragment
VARIANTS = {
    "pyo3-abi3-tests": ("pyo3", True, True, "-abi3-"),
    "pyo3-perversion": ("pyo3", False, False, "-cp3"),
    "cffi-tests": ("cffi", True, True, "-py3-none-"),
    "uniffi-tests": ("uniffi", True, True, "-py3-none-"),
}


def _render(name: str, out: Path, **options: Any) -> Path:
    opts = {**FLEX.default_options, **options}
    SkbuildProjectGenerator(
        name, FLEX.template_type, out, context={"options": opts}, update_deps=False
    ).generate()
    return out


def _run(cmd: list[str], cwd: Path) -> None:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, (
        f"{' '.join(cmd)} failed:\n{proc.stdout}\n{proc.stderr}"
    )


class TestResolve:
    def test_defaults(self):
        m = resolve({})
        assert (m.bindings, m.abi3, m.rust_tests) == ("pyo3", True, False)
        assert not m.generated_module

    def test_abi3_applies_only_to_pyo3(self):
        assert not resolve({"bindings": "cffi", "abi3": True}).abi3
        assert resolve({"bindings": "uniffi"}).generated_module

    def test_rejects_unknown_bindings(self):
        with pytest.raises(ValueError, match="Invalid bindings: 'swig'"):
            resolve({"bindings": "swig"})

    def test_rejects_non_boolean_flags(self):
        with pytest.raises(ValueError, match="'rust_tests' must be true or false"):
            resolve({"rust_tests": "yes"})


@pytest.mark.parametrize("variant", sorted(VARIANTS))
def test_flex_variant_files(tmp_path, variant):
    """Each option combination renders a consistent crate and pyproject."""
    bindings, abi3, rust_tests, _ = VARIANTS[variant]
    out = _render(
        "fx", tmp_path / "fx", bindings=bindings, abi3=abi3, rust_tests=rust_tests
    )
    generated = bindings != "pyo3"

    pyproject = tomllib.loads((out / "pyproject.toml").read_text())
    maturin = pyproject["tool"]["maturin"]
    assert maturin["module-name"] == "fx._core"
    assert maturin.get("bindings", "pyo3") == bindings
    assert ("src/fx/_core/**" in maturin["exclude"]) is generated
    assert ("exclude" in pyproject["tool"]["mypy"]) is generated
    deps = pyproject["project"].get("dependencies", [])
    assert any(d.startswith("cffi>=") for d in deps) is (bindings == "cffi")

    cargo = tomllib.loads((out / "Cargo.toml").read_text())
    assert cargo["lib"] == {"name": "_core", "crate-type": ["cdylib"]}
    if bindings == "pyo3":
        pyo3 = cargo["dependencies"]["pyo3"]
        assert ("abi3-py310" in pyo3["features"]) is abi3
        # Optional pyo3 is what lets `cargo test --no-default-features` skip libpython.
        assert pyo3.get("optional", False) is rust_tests
    else:
        assert "pyo3" not in cargo.get("dependencies", {})
    assert (out / "uniffi-bindgen.rs").exists() is (bindings == "uniffi")
    assert ("bin" in cargo) is (bindings == "uniffi")

    lib_rs = (out / "src/lib.rs").read_text()
    assert ("#[cfg(test)]" in lib_rs) is rust_tests

    makefile = (out / "Makefile").read_text()
    assert ("cargo test --no-default-features" in makefile) is rust_tests
    assert ("rm -rf src/fx/_core/" in makefile) is generated
    ci = (out / ".github/workflows/ci.yml").read_text()
    assert ("cargo test --no-default-features" in ci) is rust_tests
    assert ("src/fx/_core/" in (out / ".gitignore").read_text()) is generated

    publish = (out / ".github/workflows/build-publish.yml").read_text()
    assert ("--find-interpreter" in publish) is (bindings == "pyo3" and not abi3)


def test_plain_recipe_matches_flex_defaults_without_rust_tests(tmp_path):
    """py/maturin renders the shared templates with pyo3, abi3, and no Rust tests."""
    plain = RECIPES["py/maturin"]
    out = tmp_path / "pm"
    SkbuildProjectGenerator(
        "pm",
        plain.template_type,
        out,
        context={"options": dict(plain.default_options)},
        update_deps=False,
    ).generate()
    cargo = tomllib.loads((out / "Cargo.toml").read_text())
    assert cargo["dependencies"]["pyo3"] == {
        "version": "0.30",
        "features": ["abi3-py310"],
    }
    assert "features" not in cargo
    assert not (out / "uniffi-bindgen.rs").exists()
    assert "test-rust" not in (out / "Makefile").read_text()


class TestFlexWorkflow:
    def _new(self, tmp_path: Path) -> Path:
        cmd_new(
            argparse.Namespace(
                name="mflex",
                recipe="py/maturin-flex",
                output=str(tmp_path / "cfg"),
                env="uv",
            )
        )
        return tmp_path / "cfg" / "project.flex.json"

    def _render(self, config: Path, out: Path) -> None:
        cmd_render(
            argparse.Namespace(
                config=str(config), output=str(out), env=None, offline=True
            )
        )

    def test_new_emits_config_with_default_options(self, tmp_path):
        data = json.loads(self._new(tmp_path).read_text())
        assert data["recipe"] == "py/maturin-flex"
        assert data["options"] == {
            "env": "uv",
            "bindings": "pyo3",
            "abi3": True,
            "rust_tests": True,
        }

    def test_render_honours_edited_options(self, tmp_path):
        config = self._new(tmp_path)
        data = json.loads(config.read_text())
        data["options"]["bindings"] = "uniffi"
        config.write_text(json.dumps(data))
        out = tmp_path / "out"
        self._render(config, out)

        assert (out / "uniffi-bindgen.rs").exists()
        assert not (out / "project.flex.json").exists()
        assert json.loads((out / "project.json").read_text())["recipe"] == (
            "py/maturin-flex"
        )

    def test_render_rejects_invalid_bindings(self, tmp_path):
        config = self._new(tmp_path)
        data = json.loads(config.read_text())
        data["options"]["bindings"] = "swig"
        config.write_text(json.dumps(data))
        out = tmp_path / "out"
        with pytest.raises(ValueError, match="Invalid bindings"):
            self._render(config, out)
        assert not out.exists()


@pytest.mark.parametrize("variant", sorted(VARIANTS))
def test_flex_variant_builds(build_project_dir_factory, build_skbuild_enabled, variant):
    """Each variant syncs, passes pytest, mypy, and cargo test, and builds its wheel."""
    if not build_skbuild_enabled:
        pytest.skip("Disabled via --skip-skbuild-build")
    if not CARGO_AVAILABLE:
        pytest.skip("cargo not available")

    bindings, abi3, rust_tests, tag = VARIANTS[variant]
    name = "mx_" + variant.replace("-", "_")
    out = _render(
        name,
        build_project_dir_factory(name),
        bindings=bindings,
        abi3=abi3,
        rust_tests=rust_tests,
    )
    _run(["uv", "sync"], out)
    _run(["uv", "run", "pytest", "-q"], out)
    _run(["uv", "run", "mypy", f"src/{name}", "tests"], out)
    _run(["uv", "run", "ruff", "check", "src", "tests"], out)
    _run(["uv", "run", "ruff", "format", "--check", "src", "tests"], out)
    if rust_tests:
        _run(["cargo", "test", "--no-default-features"], out)
    # A wheel built after an editable install must not collide with the
    # generated module that install left in src/.
    _run(["uv", "build"], out)

    wheels = list((out / "dist").glob("*.whl"))
    assert len(wheels) == 1, wheels
    assert tag in wheels[0].name, wheels[0].name
    listing = subprocess.run(
        ["unzip", "-Z1", str(wheels[0])], capture_output=True, text=True, check=True
    ).stdout
    assert ".pyc" not in listing
