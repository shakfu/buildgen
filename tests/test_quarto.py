"""Tests for the quarto/* recipes."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from buildgen.cli.main import main
from buildgen.common.config import UserConfig
from buildgen.common.toolchain import required_tools
from buildgen.quarto.generator import QuartoProjectGenerator
from buildgen.recipes import RECIPES

QUARTO_AVAILABLE = shutil.which("quarto") is not None
MAKE_AVAILABLE = shutil.which("make") is not None
# Quarto also finds TinyTeX off PATH; this check only errs toward skipping.
LATEX_AVAILABLE = any(shutil.which(e) for e in ("lualatex", "xelatex", "pdflatex"))
LATEX_FORMATS = {"pdf", "beamer"}

QUARTO_RECIPES = sorted(n for n, r in RECIPES.items() if r.build_system == "quarto")

# Project recipes (with _quarto.yml): the project.type each expects; the
# default type has none.
PROJECT_TYPES = {
    "quarto/project": None,
    "quarto/website": "website",
    "quarto/blog": "website",
    "quarto/book": "book",
    "quarto/manuscript": "manuscript",
}


# Single-file recipes (no _quarto.yml): format -> output files, for a
# document named my-proj, written next to the source.
SINGLE_OUTPUTS = {
    "quarto/document": {
        "html": ["my-proj.html"],
        "pdf": ["my-proj.pdf"],
        "docx": ["my-proj.docx"],
        "typst": ["my-proj-typst.pdf"],
    },
    "quarto/presentation": {
        "revealjs": ["my-proj.html"],
        "beamer": ["my-proj.pdf"],
        "pptx": ["my-proj.pptx"],
    },
    "quarto/dashboard": {"dashboard": ["my-proj.html"]},
}

PROJECT_DOCS = ["index", "analysis", "notes/meeting"]
PROJECT_EXT = {"html": "html", "pdf": "pdf", "docx": "docx"}

# Recipes whose outputs are checked file by file after a render.
FORMAT_OUTPUTS = {
    **SINGLE_OUTPUTS,
    "quarto/project": {
        fmt: [f"{doc}.{ext}" for doc in PROJECT_DOCS]
        for fmt, ext in PROJECT_EXT.items()
    },
    "quarto/book": {
        "html": ["index.html"],
        "pdf": ["my-proj.pdf"],
        "epub": ["my-proj.epub"],
    },
}


def _generate(recipe: str, out: Path, **kwargs) -> Path:
    QuartoProjectGenerator("my-proj", recipe, out, **kwargs).generate()
    return out


def test_every_recipe_is_project_or_single_file():
    assert not set(PROJECT_TYPES) & set(SINGLE_OUTPUTS)
    assert sorted({*PROJECT_TYPES, *SINGLE_OUTPUTS}) == QUARTO_RECIPES


def test_single_file_outputs_match_generator():
    for recipe, outputs in SINGLE_OUTPUTS.items():
        expected = sorted(n for names in outputs.values() for n in names)
        listed = QuartoProjectGenerator.OUTPUTS[recipe]
        assert sorted(o.format(name="my-proj") for o in listed) == expected


def test_required_tools():
    assert required_tools("quarto", "markdown") == {"quarto", "make"}


class TestNameValidation:
    @pytest.mark.parametrize("name", ["site", "my-site", "notes.v2", "2026_talk"])
    def test_accepts(self, name, tmp_path):
        QuartoProjectGenerator(name, "quarto/website", tmp_path)

    @pytest.mark.parametrize(
        "name", ["", "../x", "a/b", "a\\b", ".hidden", "-x", 'a"b', "a b"]
    )
    def test_rejects(self, name, tmp_path):
        with pytest.raises(ValueError, match="Invalid project name"):
            QuartoProjectGenerator(name, "quarto/website", tmp_path)

    def test_unknown_recipe(self, tmp_path):
        with pytest.raises(ValueError, match="Invalid recipe"):
            QuartoProjectGenerator("x", "cpp/executable", tmp_path)


@pytest.mark.parametrize("recipe", sorted(PROJECT_TYPES))
class TestGeneratedProject:
    def test_quarto_yml(self, recipe, tmp_path):
        project = _generate(recipe, tmp_path)
        config = yaml.safe_load((project / "_quarto.yml").read_text())

        assert config["project"].get("type") == PROJECT_TYPES[recipe]
        output_dir = QuartoProjectGenerator.OUTPUT_DIRS[recipe]
        assert config["project"]["output-dir"] == output_dir

    def test_makefile_and_gitignore_name_the_output_dir(self, recipe, tmp_path):
        project = _generate(recipe, tmp_path)
        output_dir = QuartoProjectGenerator.OUTPUT_DIRS[recipe]

        makefile = (project / "Makefile").read_text()
        assert f"OUTPUT_DIR ?= {output_dir}\n" in makefile
        # _freeze/ holds executed results and belongs in version control.
        assert (
            "_freeze" not in re.findall(r"^clean:\n\t(.*)$", makefile, re.MULTILINE)[0]
        )
        gitignore = (project / ".gitignore").read_text().splitlines()
        assert f"/{output_dir}/" in gitignore
        assert "/.quarto/" in gitignore


@pytest.mark.parametrize("recipe", sorted(SINGLE_OUTPUTS))
class TestGeneratedSingleFile:
    def test_has_no_quarto_yml(self, recipe, tmp_path):
        project = _generate(recipe, tmp_path)
        assert not (project / "_quarto.yml").exists()
        assert sorted(p.name for p in project.glob("*.qmd")) == ["my-proj.qmd"]

    def test_makefile_and_gitignore_name_the_outputs(self, recipe, tmp_path):
        project = _generate(recipe, tmp_path)
        outputs = [n for names in SINGLE_OUTPUTS[recipe].values() for n in names]

        makefile = (project / "Makefile").read_text()
        # Outside a project, a bare `quarto render` renders nothing.
        assert "SOURCE ?= my-proj.qmd\n" in makefile
        clean = re.findall(r"^clean:\n\t(.*)$", makefile, re.MULTILINE)[0]
        gitignore = (project / ".gitignore").read_text().splitlines()
        for name in outputs:
            assert name in clean.split()
            assert f"/{name}" in gitignore


@pytest.mark.parametrize("recipe", QUARTO_RECIPES)
def test_qmd_front_matter_parses(recipe, tmp_path):
    project = _generate(recipe, tmp_path)
    for qmd in project.rglob("*.qmd"):
        text = qmd.read_text()
        if text.startswith("---\n"):
            yaml.safe_load(text.split("---\n")[1])


def _front_matter(path: Path) -> dict:
    return yaml.safe_load(path.read_text().split("---\n")[1])


# Where each recipe puts the user's name.
AUTHOR_FIELDS = {
    "quarto/book": lambda p: yaml.safe_load((p / "_quarto.yml").read_text())["book"][
        "author"
    ],
    "quarto/manuscript": lambda p: _front_matter(p / "index.qmd")["authors"][0]["name"],
    "quarto/blog": lambda p: _front_matter(p / "posts/welcome/index.qmd")["author"],
    "quarto/project": lambda p: yaml.safe_load((p / "_quarto.yml").read_text())[
        "author"
    ],
    **{
        r: lambda p: _front_matter(p / "my-proj.qmd")["author"]
        for r in ("quarto/document", "quarto/presentation", "quarto/dashboard")
    },
}


@pytest.mark.parametrize("recipe", sorted(AUTHOR_FIELDS))
def test_user_name_is_yaml_escaped(recipe, tmp_path):
    author = 'Ada "the" Lovelace: #1'
    project = _generate(recipe, tmp_path, user_config=UserConfig(user_name=author))
    assert AUTHOR_FIELDS[recipe](project) == author


def test_book_author_from_user_config(tmp_path):
    project = _generate(
        "quarto/book", tmp_path, user_config=UserConfig(user_name="Ada")
    )
    config = yaml.safe_load((project / "_quarto.yml").read_text())
    assert config["book"]["author"] == "Ada"


def test_book_omits_author_without_user_config(tmp_path):
    project = _generate("quarto/book", tmp_path)
    config = yaml.safe_load((project / "_quarto.yml").read_text())
    assert "author" not in config["book"]


@pytest.mark.parametrize("recipe", sorted(SINGLE_OUTPUTS))
def test_single_source_formats(recipe, tmp_path):
    """The .qmd header configures exactly the recipe's formats."""
    project = _generate(recipe, tmp_path)
    header = _front_matter(project / "my-proj.qmd")
    declared = set(header.get("format", {"html": None}))
    assert declared == set(SINGLE_OUTPUTS[recipe])


def test_project_shares_options_across_documents(tmp_path):
    """quarto/project sets formats once in _quarto.yml for every document."""
    project = _generate("quarto/project", tmp_path)
    config = yaml.safe_load((project / "_quarto.yml").read_text())
    assert set(config["format"]) == set(PROJECT_EXT)
    assert config["toc"] is True
    assert config["number-sections"] is True
    for doc in PROJECT_DOCS:
        assert "format" not in _front_matter(project / f"{doc}.qmd")
    notes = yaml.safe_load((project / "notes/_metadata.yml").read_text())
    assert notes == {"number-sections": False, "toc": False}


def test_local_template_override(tmp_path):
    override = tmp_path / ".buildgen/templates/quarto/website/about.qmd.mako"
    override.parent.mkdir(parents=True)
    override.write_text("overridden ${name}\n")
    out = tmp_path / "site"
    QuartoProjectGenerator(
        "site", "quarto/website", out, project_dir=tmp_path
    ).generate()
    assert (out / "about.qmd").read_text() == "overridden site\n"


class TestCli:
    def test_new_creates_project(self, tmp_path, monkeypatch, capsys):
        out = tmp_path / "my-book"
        monkeypatch.setattr(
            sys,
            "argv",
            ["buildgen", "new", "my-book", "-r", "quarto/book", "-o", str(out)],
        )
        main()
        assert (out / "_quarto.yml").is_file()
        assert "Created quarto/book project" in capsys.readouterr().out

    def test_new_dry_run_writes_nothing(self, tmp_path, monkeypatch):
        out = tmp_path / "site"
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "buildgen",
                "new",
                "site",
                "-r",
                "quarto/website",
                "-o",
                str(out),
                "--dry-run",
            ],
        )
        main()
        assert not out.exists()

    def test_list_category(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["buildgen", "list", "-c", "quarto"])
        main()
        listed = capsys.readouterr().out
        for recipe in QUARTO_RECIPES:
            assert recipe in listed
        assert "cpp/" not in listed


def _make(project: Path, *args: str) -> None:
    proc = subprocess.run(
        ["make", *args],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr


@pytest.mark.skipif(
    not (QUARTO_AVAILABLE and MAKE_AVAILABLE), reason="quarto or make not on PATH"
)
@pytest.mark.parametrize("recipe", QUARTO_RECIPES)
def test_recipe_renders(build_project_dir_factory, recipe):
    """`make render` writes every format to its own file; `make clean` removes them.

    Project recipes write to their output dir, single-file recipes next to the
    source. LaTeX formats (pdf, beamer) are skipped when no LaTeX engine is on
    PATH.
    """
    project = _generate(recipe, build_project_dir_factory(recipe.replace("/", "_")))
    single = recipe in SINGLE_OUTPUTS
    output_dir = (
        project if single else project / QuartoProjectGenerator.OUTPUT_DIRS[recipe]
    )

    outputs = FORMAT_OUTPUTS.get(recipe)
    if outputs is None:
        # Website-like projects declare html only.
        _make(project, "render")
        assert list(output_dir.rglob("*.html"))
    elif LATEX_AVAILABLE:
        _make(project, "render")
    else:
        for fmt in set(outputs) - LATEX_FORMATS:
            _make(project, "render", f"QUARTO_FLAGS=--to {fmt}")
        outputs = {f: o for f, o in outputs.items() if f not in LATEX_FORMATS}

    for fmt, names in (outputs or {}).items():
        for name in names:
            assert (output_dir / name).is_file(), f"{fmt}: missing {name}"
    if recipe == "quarto/project":
        # notes/_metadata.yml overrides the project's numbering and TOC.
        index = (output_dir / "index.html").read_text()
        notes = (output_dir / "notes/meeting.html").read_text()
        assert "header-section-number" in index
        assert 'id="TOC"' in index
        assert "header-section-number" not in notes
        assert 'id="TOC"' not in notes
        # Sources are not copied into the output.
        assert not list(output_dir.rglob("*.qmd"))
    assert not list(output_dir.rglob("TODO.html")), "TODO.md was rendered"

    _make(project, "clean")
    if single:
        leftover = [n for names in (outputs or {}).values() for n in names]
        assert not [n for n in leftover if (project / n).exists()]
        assert not (project / "my-proj_files").exists()
    else:
        assert not output_dir.exists()
    assert not (project / ".quarto").exists()


def test_manuscript_front_matter(tmp_path):
    """Scholarly metadata from the manuscripts guide; author from user config."""
    project = _generate(
        "quarto/manuscript",
        tmp_path,
        user_config=UserConfig(user_name="Ada", user_email='a"da@example.com'),
    )
    header = _front_matter(project / "index.qmd")
    author = header["authors"][0]
    assert author["name"] == "Ada"
    assert author["email"] == 'a"da@example.com'
    assert author["corresponding"] is True
    for key in ("abstract", "keywords", "date", "bibliography", "number-sections"):
        assert key in header


def test_manuscript_omits_email_without_user_config(tmp_path):
    project = _generate(
        "quarto/manuscript", tmp_path, user_config=UserConfig(user_name="Ada")
    )
    assert "email" not in _front_matter(project / "index.qmd")["authors"][0]


def test_blog_links_its_feed(tmp_path):
    project = _generate("quarto/blog", tmp_path)
    config = yaml.safe_load((project / "_quarto.yml").read_text())
    assert {"icon": "rss", "href": "index.xml"} in config["website"]["navbar"]["right"]
    assert _front_matter(project / "index.qmd")["listing"]["feed"] is True
