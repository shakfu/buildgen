"""Tests for the lifecycle and configuration features added after 0.3.x."""

from __future__ import annotations

import json
from argparse import Namespace

import pytest

from buildgen.cli.commands import cmd_generate, cmd_new
from buildgen.common.deps import load_lock, write_lock
from buildgen.common.project import (
    DependencyConfig,
    ProjectConfig,
    TargetConfig,
    ToolchainProfile,
)
from buildgen.common.toolchain import ToolInfo, diagnostics_json, required_tools


def test_tool_diagnostics_are_machine_readable():
    data = json.loads(
        diagnostics_json({"cmake": ToolInfo("cmake", "/bin/cmake", "cmake 4")})
    )
    assert data["tools"]["cmake"]["available"] is True
    assert required_tools("python", "python") == {"python", "uv"}


def test_lock_round_trip_is_sorted_and_complete(tmp_path):
    path = tmp_path / "buildgen.lock"
    write_lock(
        path,
        recipe="py/nodeps",
        dependencies={"z": "2", "a": "1"},
        buildgen_version="0.4.0",
    )
    data = load_lock(path)
    assert data["dependencies"] == {"a": "1", "z": "2"}
    assert data["recipe"] == "py/nodeps"


def test_validation_reports_unknown_and_duplicate_fields():
    source = {
        "name": "demo",
        "unknown": True,
        "targets": [{"name": "app"}, {"name": "app", "type": "invalid"}],
    }
    config = ProjectConfig.from_dict(source)
    errors = config.validate(source)
    assert "unknown key: unknown" in errors
    assert "duplicate target name: app" in errors
    assert any("type is invalid" in error for error in errors)


def test_presets_include_profiles_and_compile_commands(tmp_path):
    config = ProjectConfig(
        name="demo",
        profile="cross",
        profiles={
            "cross": ToolchainProfile(
                cc="arm-none-eabi-gcc",
                cmake_variables={"CMAKE_SYSTEM_NAME": "Generic"},
            )
        },
        targets=[TargetConfig(name="app", sources=["main.cpp"])],
    )
    path = tmp_path / "CMakePresets.json"
    config.generate_cmake_presets(path)
    data = json.loads(path.read_text())
    assert data["version"] == 6
    assert (
        data["configurePresets"][0]["cacheVariables"]["CMAKE_SYSTEM_NAME"] == "Generic"
    )
    assert (
        data["configurePresets"][0]["cacheVariables"]["CMAKE_EXPORT_COMPILE_COMMANDS"]
        == "ON"
    )


def test_profile_and_dependency_provider_reach_cmake(tmp_path):
    config = ProjectConfig(
        name="demo",
        profile="clang",
        profiles={
            "clang": ToolchainProfile(cxx="clang++", toolchain_file="cross.cmake")
        },
        dependencies=[DependencyConfig(name="fmt", provider="system", version="10")],
        targets=[TargetConfig(name="app", sources=["main.cpp"])],
    )
    output = tmp_path / "CMakeLists.txt"
    config.generate_cmake(output)
    content = output.read_text()
    assert "find_package(fmt 10 REQUIRED)" in content
    # CMake reads compiler and toolchain settings while project() runs and
    # ignores them afterwards, so they must be emitted above it.
    lines = content.splitlines()
    project_line = next(
        i for i, line in enumerate(lines) if line.startswith("project(")
    )
    compiler_line = next(
        i for i, line in enumerate(lines) if "CMAKE_CXX_COMPILER" in line
    )
    toolchain_line = next(
        i for i, line in enumerate(lines) if "CMAKE_TOOLCHAIN_FILE" in line
    )
    assert compiler_line < project_line
    assert toolchain_line < project_line


def test_unknown_profile_is_rejected_at_generation(tmp_path):
    config = ProjectConfig(name="demo", profile="missing")
    with pytest.raises(ValueError, match="unknown profile"):
        config.generate_cmake(tmp_path / "CMakeLists.txt")


def test_fetchcontent_without_source_is_rejected(tmp_path):
    config = ProjectConfig(
        name="demo",
        dependencies=[DependencyConfig(name="fmt", provider="fetchcontent")],
    )
    with pytest.raises(ValueError, match="needs git_repository or url"):
        config.generate_cmake(tmp_path / "CMakeLists.txt")


def test_source_dependencies_are_not_linked_in_the_makefile(tmp_path):
    config = ProjectConfig(
        name="demo",
        dependencies=[
            DependencyConfig(name="fmt", url="https://example.test/fmt.zip"),
            DependencyConfig(name="ssl", provider="system"),
        ],
        targets=[TargetConfig(name="app", sources=["main.cpp"])],
    )
    output = tmp_path / "Makefile"
    config.generate_makefile(output)
    content = output.read_text()
    assert "-lssl" in content
    assert "-lfmt" not in content


def test_unknown_provider_is_rejected_by_both_generators(tmp_path):
    config = ProjectConfig(
        name="demo",
        dependencies=[DependencyConfig(name="fmt", provider="vcpkg")],
        targets=[TargetConfig(name="app", sources=["main.cpp"])],
    )
    with pytest.raises(ValueError, match="unknown provider vcpkg"):
        config.generate_cmake(tmp_path / "CMakeLists.txt")
    with pytest.raises(ValueError, match="unknown provider vcpkg"):
        config.generate_makefile(tmp_path / "Makefile")


def test_lock_from_a_future_format_is_rejected(tmp_path):
    path = tmp_path / "buildgen.lock"
    path.write_text(json.dumps({"lock_version": 99, "dependencies": {}}))
    with pytest.raises(ValueError, match="Unsupported buildgen lock version"):
        load_lock(path)


def test_lock_pins_generated_dependencies_without_offline(tmp_path):
    from buildgen.skbuild.generator import SkbuildProjectGenerator

    output_dir = tmp_path / "demo"
    output_dir.mkdir()
    write_lock(
        output_dir / "buildgen.lock",
        recipe="py/nodeps",
        dependencies={"ruff": "0.0.1"},
        buildgen_version="0.4.0",
    )
    gen = SkbuildProjectGenerator("demo", "py/nodeps", output_dir, update_deps=True)
    # The lock wins over a PyPI query; packages it predates keep their default.
    assert gen.context["dep_versions"]["ruff"] == "0.0.1"
    assert gen.context["dep_versions"]["pytest"] != "0"


def test_fetchcontent_provider_preserves_url(tmp_path):
    config = ProjectConfig(
        name="demo",
        dependencies=[
            DependencyConfig(
                name="fmt", provider="fetchcontent", url="https://example.test/fmt.zip"
            )
        ],
    )
    output = tmp_path / "CMakeLists.txt"
    config.generate_cmake(output)
    assert "URL https://example.test/fmt.zip" in output.read_text()


def test_new_dry_run_does_not_write(tmp_path):
    args = Namespace(
        name="demo",
        recipe="cpp/executable",
        output=str(tmp_path / "demo"),
        env=None,
        no_update_deps=True,
        offline=True,
        force=False,
        dry_run=True,
    )
    cmd_new(args)
    assert not (tmp_path / "demo").exists()


def test_generate_config_refuses_to_replace_an_existing_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "project.json").write_text("user content\n")
    args = Namespace(
        config="project.json", from_config=None, dry_run=False, force=False
    )
    with pytest.raises(FileExistsError):
        cmd_generate(args)
    assert (tmp_path / "project.json").read_text() == "user content\n"


def test_generate_refuses_existing_files_without_force(tmp_path, monkeypatch):
    config_path = tmp_path / "project.json"
    config_path.write_text(json.dumps({"name": "demo", "targets": []}))
    (tmp_path / "Makefile").write_text("user content\n")
    monkeypatch.chdir(tmp_path)
    args = Namespace(
        config=None,
        from_config=str(config_path),
        makefile=True,
        cmake=False,
        dry_run=False,
        force=False,
        presets=False,
        profile=None,
    )
    with pytest.raises(FileExistsError):
        cmd_generate(args)
    assert (tmp_path / "Makefile").read_text() == "user content\n"
