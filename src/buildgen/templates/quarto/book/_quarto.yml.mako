<%
import json
from datetime import date
_author = user.get("name") if user else None
%>\
project:
  type: book
  # Every page except TODO.md (README.md is excluded by default).
  render:
    - "**/*.qmd"
    - "**/*.md"
    - "!TODO.md"
  output-dir: ${output_dir}

book:
  title: "${name}"
% if _author:
  author: ${json.dumps(_author)}
% endif
  date: "${date.today().isoformat()}"
  chapters:
    - index.qmd
    - intro.qmd
    - summary.qmd
    - references.qmd

bibliography: references.bib

format:
  html:
    theme:
      - cosmo
      - brand
  # Requires a LaTeX distribution (quarto install tinytex).
  pdf:
    documentclass: scrreprt
  epub:
    # Add a cover with cover-image: cover.png
    toc: true
