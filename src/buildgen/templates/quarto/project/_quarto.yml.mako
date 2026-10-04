<%
import json
_author = user.get("name") if user else None
%>\
project:
  title: "${name}"
  # Every page except TODO.md (README.md is excluded by default).
  render:
    - "**/*.qmd"
    - "**/*.md"
    - "!TODO.md"
  output-dir: ${output_dir}

# Options below apply to every document in the project. A directory's
# _metadata.yml, then a document's own header, override or extend them.
% if _author:
author: ${json.dumps(_author)}
% endif
toc: true
number-sections: true
bibliography: references.bib

format:
  html:
    css: styles.css
    html-math-method: katex
  pdf:
    documentclass: report
    margin-left: 30mm
    margin-right: 30mm
  docx:
    toc-depth: 2
