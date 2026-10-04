"""Quarto project generator using templates.

Generates Quarto projects (https://quarto.org/docs/projects/quarto-projects.html)
from templates in templates/quarto/*.
"""

import re
from pathlib import Path
from typing import Any, ClassVar

from buildgen.common.config import UserConfig
from buildgen.templates.generator import TemplateProjectGenerator

# Safe as a path component and inside a double-quoted YAML scalar.
_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")

_COMMON = {
    ".gitignore": "common/gitignore.quarto.mako",
    "Makefile": "common/Makefile.quarto.mako",
    "TODO.md": "common/TODO.md.mako",
    "_quarto.yml": "_quarto.yml.mako",
}

# Single-file recipes: no _quarto.yml, so Quarto renders the document on its
# own and writes each format next to the source.
_SINGLE = {
    ".gitignore": "common/gitignore.quarto-doc.mako",
    "Makefile": "common/Makefile.quarto-doc.mako",
    "TODO.md": "common/TODO.md.mako",
}


class QuartoProjectGenerator(TemplateProjectGenerator):
    """Generate a Quarto project: _quarto.yml, sources, and a Makefile frontend.

    Usage:
        gen = QuartoProjectGenerator("mybook", "quarto/book")
        files = gen.generate()
    """

    TEMPLATE_FILES: ClassVar[dict[str, dict[str, str]]] = {
        "quarto/project": {
            **_COMMON,
            "index.qmd": "index.qmd.mako",
            "analysis.qmd": "analysis.qmd.mako",
            "notes/_metadata.yml": "notes/_metadata.yml.mako",
            "notes/meeting.qmd": "notes/meeting.qmd.mako",
            "references.bib": "references.bib.mako",
            "styles.css": "styles.css.mako",
        },
        "quarto/document": {
            **_SINGLE,
            "${name}.qmd": "document.qmd.mako",
            "references.bib": "references.bib.mako",
        },
        "quarto/presentation": {
            **_SINGLE,
            "${name}.qmd": "presentation.qmd.mako",
        },
        "quarto/dashboard": {
            **_SINGLE,
            "${name}.qmd": "dashboard.qmd.mako",
        },
        "quarto/website": {
            **_COMMON,
            "index.qmd": "index.qmd.mako",
            "about.qmd": "about.qmd.mako",
            "styles.css": "styles.css.mako",
        },
        "quarto/blog": {
            **_COMMON,
            "index.qmd": "index.qmd.mako",
            "about.qmd": "about.qmd.mako",
            "styles.css": "styles.css.mako",
            "posts/_metadata.yml": "posts/_metadata.yml.mako",
            "posts/welcome/index.qmd": "posts/welcome/index.qmd.mako",
        },
        "quarto/book": {
            **_COMMON,
            "index.qmd": "index.qmd.mako",
            "intro.qmd": "intro.qmd.mako",
            "summary.qmd": "summary.qmd.mako",
            "references.qmd": "references.qmd.mako",
            "references.bib": "references.bib.mako",
        },
        "quarto/manuscript": {
            **_COMMON,
            "index.qmd": "index.qmd.mako",
            "references.bib": "references.bib.mako",
        },
    }

    # Project recipes: Quarto's per-type default output-dir; _quarto.yml
    # states it explicitly so the Makefile's clean target and the config
    # agree. The default type renders in place unless told otherwise, so it
    # gets _output.
    OUTPUT_DIRS: ClassVar[dict[str, str]] = {
        "quarto/project": "_output",
        "quarto/website": "_site",
        "quarto/blog": "_site",
        "quarto/book": "_book",
        "quarto/manuscript": "_manuscript",
    }

    # Single-file recipes: the files one render writes, one per format.
    OUTPUTS: ClassVar[dict[str, list[str]]] = {
        "quarto/document": [
            "{name}.html",
            "{name}.pdf",
            "{name}.docx",
            "{name}-typst.pdf",
        ],
        "quarto/presentation": ["{name}.html", "{name}.pdf", "{name}.pptx"],
        "quarto/dashboard": ["{name}.html"],
    }

    def __init__(
        self,
        name: str,
        recipe: str,
        output_dir: Path | None = None,
        project_dir: Path | None = None,
        context: dict[str, Any] | None = None,
        user_config: UserConfig | None = None,
    ):
        super().__init__(name, recipe, output_dir, project_dir, context, user_config)
        if recipe in self.OUTPUTS:
            outputs = [o.format(name=name) for o in self.OUTPUTS[recipe]]
            self.context.setdefault("outputs", outputs)
        else:
            self.context.setdefault("output_dir", self.OUTPUT_DIRS[recipe])

    @staticmethod
    def validate_name(name: str) -> None:
        """Raise ValueError unless *name* matches ``[A-Za-z0-9][A-Za-z0-9._-]*``."""
        if not _NAME_RE.fullmatch(name):
            raise ValueError(
                f"Invalid project name: {name!r}. Use letters, digits, '.', '_' "
                "or '-', starting with a letter or digit."
            )
