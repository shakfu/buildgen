"""Tests for the CLI command layer and the config-driven generation path.

The `generate --config` / `generate --from` round trip and the C-language
Makefile output are covered here because they are the paths where a defect
produces a *silently wrong build* rather than an error.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from buildgen.cli import cmd_generate
from buildgen.cli.main import main
from buildgen.common.project import ProjectConfig

CC_AVAILABLE = shutil.which("cc") is not None or shutil.which("gcc") is not None
MAKE_AVAILABLE = shutil.which("make") is not None


def _generate_config(path: Path) -> dict:
    """Run `generate --config <path>` and return the parsed result."""
    cmd_generate(
        argparse.Namespace(
            config=str(path), from_config=None, makefile=False, cmake=False
        )
    )
    assert path.exists()
    if path.suffix in (".yaml", ".yml"):
        import yaml

        return yaml.safe_load(path.read_text())
    return json.loads(path.read_text())


class TestGenerateConfigRoundTrip:
    """`generate --config` must emit a schema `ProjectConfig` actually reads."""

    @pytest.mark.parametrize("filename", ["project.json", "project.yaml"])
    def test_no_keys_dropped(self, tmp_path, filename):
        """Every emitted key survives load -> to_dict."""
        config_path = tmp_path / filename
        emitted = _generate_config(config_path)

        round_tripped = ProjectConfig.load(config_path).to_dict()
        dropped = sorted(set(emitted) - set(round_tripped))
        assert not dropped, f"keys silently dropped on load: {dropped}"

    @pytest.mark.parametrize("filename", ["project.json", "project.yaml"])
    def test_emitted_template_loads(self, tmp_path, filename):
        """The untouched template loads into a usable config."""
        config_path = tmp_path / filename
        _generate_config(config_path)

        config = ProjectConfig.load(config_path)
        assert config.name == "myproject"
        assert config.cxx_standard == 17
        assert [t.name for t in config.targets] == ["myapp"]

    def test_edited_flags_reach_generated_build_files(self, tmp_path, monkeypatch):
        """Flags written into the template must appear in both generators.

        This is the regression guard for the schema mismatch: the template used
        to emit `cflags`/`cxxflags`/`ldflags`/`ldlibs`, none of which the loader
        read, so edits to those keys vanished without a warning.
        """
        config_path = tmp_path / "project.json"
        data = _generate_config(config_path)

        data["compile_options"] = ["-Wall", "-Wextra"]
        data["compile_definitions"] = ["MYPROJECT_FEATURE=1"]
        data["link_options"] = ["-Wl,--as-needed"]
        # MakefileGenerator.check_dir validates include dirs against the
        # filesystem, so the directory has to exist before generation.
        data["include_dirs"] = ["include"]
        (tmp_path / "include").mkdir()
        config_path.write_text(json.dumps(data, indent=2))

        monkeypatch.chdir(tmp_path)
        cmd_generate(
            argparse.Namespace(
                config=None,
                from_config=str(config_path),
                makefile=False,
                cmake=False,
            )
        )

        makefile = (tmp_path / "Makefile").read_text()
        cmake = (tmp_path / "CMakeLists.txt").read_text()
        for fragment in ("-Wall", "-Wextra", "-DMYPROJECT_FEATURE=1"):
            assert fragment in makefile, f"{fragment} missing from Makefile"
        assert "-Wl,--as-needed" in makefile
        for fragment in ("-Wall", "-Wextra"):
            assert fragment in cmake, f"{fragment} missing from CMakeLists.txt"

    def test_generate_requires_a_mode(self, tmp_path):
        """Neither --config nor --from is an error, not a silent no-op."""
        with pytest.raises(SystemExit) as excinfo:
            cmd_generate(
                argparse.Namespace(
                    config=None, from_config=None, makefile=False, cmake=False
                )
            )
        assert excinfo.value.code == 1


class TestCMakefileGenerationForC:
    """The Makefile generator must respect the project's language settings."""

    @staticmethod
    def _c_config(**overrides) -> dict:
        config = {
            "name": "cproj",
            "languages": ["C"],
            "c_standard": 11,
            "cc": "gcc",
            "targets": [
                {"name": "app", "type": "executable", "sources": ["src/main.c"]}
            ],
        }
        config.update(overrides)
        return config

    def _write_makefile(self, tmp_path: Path, config: dict) -> str:
        config_path = tmp_path / "project.json"
        config_path.write_text(json.dumps(config))
        makefile = tmp_path / "Makefile"
        ProjectConfig.load(config_path).generate_makefile(makefile)
        return makefile.read_text()

    def test_c_project_emits_c_toolchain(self, tmp_path):
        content = self._write_makefile(tmp_path, self._c_config())
        assert "CC = gcc" in content
        assert "-std=c11" in content
        assert "%.o: %.c" in content
        assert "$(CC) $(CFLAGS) -c $< -o $@" in content

    def test_c_only_target_links_with_cc(self, tmp_path):
        content = self._write_makefile(tmp_path, self._c_config())
        assert "$(CC) $(CFLAGS) -o $@" in content
        assert "$(CXX) $(CXXFLAGS) -o $@" not in content

    def test_mixed_target_links_with_cxx(self, tmp_path):
        config = self._c_config(
            languages=["C", "CXX"],
            cxx_standard=17,
            targets=[
                {
                    "name": "app",
                    "type": "executable",
                    "sources": ["src/main.cpp", "src/util.c"],
                }
            ],
        )
        content = self._write_makefile(tmp_path, config)
        assert "$(CXX) $(CXXFLAGS) -o $@" in content
        assert "%.o: %.cpp" in content
        assert "%.o: %.c" in content
        assert "-std=c11" in content
        assert "-std=c++17" in content

    def test_shared_library_objects_are_position_independent(self, tmp_path):
        config = self._c_config(
            targets=[{"name": "mylib", "type": "shared", "sources": ["src/lib.c"]}]
        )
        content = self._write_makefile(tmp_path, config)
        assert "-fPIC" in content
        assert "$(CC) -shared -o $@" in content

    def test_no_fpic_without_shared_targets(self, tmp_path):
        content = self._write_makefile(tmp_path, self._c_config())
        assert "-fPIC" not in content

    def test_namespaced_dependency_is_not_linked_verbatim(self, tmp_path):
        """A CMake-style name must not become `-lfmt::fmt`."""
        config = self._c_config(dependencies=[{"name": "fmt::fmt"}])
        content = self._write_makefile(tmp_path, config)
        assert "-lfmt::fmt" not in content
        assert "-lfmt" in content

    def test_link_libraries_reach_the_link_line(self, tmp_path):
        config = self._c_config(
            dependencies=[{"name": "m"}],
            targets=[
                {
                    "name": "app",
                    "type": "executable",
                    "sources": ["src/main.c"],
                    "link_libraries": ["Threads::Threads", "-ldl"],
                }
            ],
        )
        content = self._write_makefile(tmp_path, config)
        assert "LDLIBS = -lm" in content
        assert "$(LDLIBS)" in content, "project dependencies never reach the link line"
        assert "-lThreads" in content
        assert "-ldl" in content

    def test_cxx_only_project_is_unchanged(self, tmp_path):
        """A pure C++ project must not gain a CC assignment or a .c rule."""
        config = {
            "name": "cxxproj",
            "cxx_standard": 17,
            "targets": [
                {"name": "app", "type": "executable", "sources": ["src/main.cpp"]}
            ],
        }
        content = self._write_makefile(tmp_path, config)
        assert "CC = " not in content
        assert "%.o: %.c\n" not in content
        assert "%.o: %.cpp" in content

    @pytest.mark.skipif(
        not (CC_AVAILABLE and MAKE_AVAILABLE), reason="needs cc/gcc and make"
    )
    def test_generated_c_makefile_builds_and_runs(self, tmp_path):
        """The end that matters: the generated Makefile actually builds C."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src/main.c").write_text(
            "#include <stdio.h>\n"
            "int lib_answer(void);\n"
            'int main(void) { printf("%d\\n", lib_answer()); return 0; }\n'
        )
        (tmp_path / "src/lib.c").write_text("int lib_answer(void) { return 42; }\n")

        config = self._c_config(
            targets=[
                {
                    "name": "app",
                    "type": "executable",
                    "sources": ["src/main.c", "src/lib.c"],
                }
            ]
        )
        self._write_makefile(tmp_path, config)

        build = subprocess.run(
            ["make"], cwd=tmp_path, capture_output=True, text=True, check=False
        )
        assert build.returncode == 0, f"make failed:\n{build.stdout}\n{build.stderr}"
        # Compilation must go through the C driver, not make's implicit rules.
        assert "gcc" in build.stdout

        run = subprocess.run(
            [str(tmp_path / "app")], capture_output=True, text=True, check=False
        )
        assert run.returncode == 0
        assert run.stdout.strip() == "42"


class TestMainDispatch:
    """Error and help paths in cli/main.py."""

    @staticmethod
    def _run(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "buildgen", *args],
            capture_output=True,
            text=True,
            check=False,
        )

    @pytest.mark.parametrize("group", ["config", "makefile", "cmake", "templates"])
    def test_bare_subcommand_group_shows_its_help(self, group):
        """A group with no subcommand prints that group's help and exits 0."""
        result = self._run(group)
        assert result.returncode == 0
        assert group in result.stdout
        assert "usage:" in result.stdout.lower()

    def test_unknown_recipe_exits_nonzero(self, tmp_path):
        result = self._run("new", "x", "-r", "py/does-not-exist", "-o", str(tmp_path))
        assert result.returncode != 0

    def test_command_error_is_reported_not_traced(self, tmp_path):
        """A failing command reports an error message, not a traceback."""
        result = self._run("render", str(tmp_path / "missing.json"))
        assert result.returncode == 1
        assert "Traceback" not in result.stderr
        assert "Error" in result.stderr or "Error" in result.stdout


class TestMainDispatchInProcess:
    """Same dispatch paths as above, run in-process so they are measurable."""

    @staticmethod
    def _main(monkeypatch, *args: str) -> int:
        monkeypatch.setattr(sys, "argv", ["buildgen", *args])
        with pytest.raises(SystemExit) as excinfo:
            main()
        code = excinfo.value.code
        return 0 if code is None else int(code)

    def test_no_command_exits_one(self, monkeypatch, capsys):
        assert self._main(monkeypatch) == 1
        assert "usage:" in capsys.readouterr().out.lower()

    @pytest.mark.parametrize("group", ["config", "makefile", "cmake", "templates"])
    def test_bare_group_prints_group_help(self, monkeypatch, capsys, group):
        assert self._main(monkeypatch, group) == 0
        out = capsys.readouterr().out
        assert "usage:" in out.lower()
        assert group in out

    def test_command_exception_becomes_error_exit(self, monkeypatch, capsys):
        """A command that raises is reported as an error, not a traceback."""

        def boom(_args):
            raise RuntimeError("deliberate failure")

        # create_parser() binds func at parser-construction time and main()
        # builds the parser itself, so patch the name the parser module reads.
        monkeypatch.setattr("buildgen.cli.parsers.cmd_list", boom)
        assert self._main(monkeypatch, "list") == 1
        assert "deliberate failure" in capsys.readouterr().err

    def test_group_with_subcommand_dispatches(self, monkeypatch, capsys):
        """A group subcommand runs its func rather than printing help."""
        monkeypatch.setattr(sys, "argv", ["buildgen", "config", "path"])
        main()
        assert ".buildgen" in capsys.readouterr().out


class TestCmdTestFlagValidation:
    """`buildgen test --test` without --build has nothing to run."""

    @staticmethod
    def _run(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "buildgen", "test", *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_test_without_build_is_an_error(self):
        result = self._run("--test")
        assert result.returncode == 1
        assert "--test requires --build" in result.stderr

    def test_short_flag_is_rejected_too(self):
        result = self._run("-t")
        assert result.returncode == 1

    def test_all_implies_build(self):
        """--all must not trip the guard; it means --build --test."""
        from buildgen.cli import cmd_test

        args = argparse.Namespace(
            build=False,
            test=False,
            all=True,
            name="nope/nope",
            category=None,
            output=None,
            keep=False,
        )
        with pytest.raises(SystemExit) as excinfo:
            cmd_test(args)
        # Fails on the unknown recipe, not on the flag guard.
        assert excinfo.value.code == 1


class TestValidationSurvivesOptimizedMode:
    """Generator input validation must not be compiled away by `python -O`."""

    def test_missing_include_dir_still_rejected_under_O(self, tmp_path):  # noqa: N802
        script = tmp_path / "check.py"
        script.write_text(
            "from buildgen.makefile.generator import MakefileGenerator\n"
            "gen = MakefileGenerator('Makefile')\n"
            "try:\n"
            "    gen.add_include_dirs('definitely-not-a-directory')\n"
            "except ValueError:\n"
            "    print('rejected')\n"
            "else:\n"
            "    print('ACCEPTED')\n"
        )
        result = subprocess.run(
            [sys.executable, "-O", str(script)],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "rejected"
