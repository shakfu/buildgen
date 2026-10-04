<%
import json
_author = user.get("name") if user else None
%>\
---
title: "${name}"
% if _author:
author: ${json.dumps(_author)}
% endif
date: today
abstract: |
  One-paragraph summary of the document.
toc: true
number-sections: true
bibliography: references.bib
format:
  html:
    theme: cosmo
    toc-location: left
    code-fold: true
    embed-resources: true
  pdf:
    documentclass: scrartcl
    papersize: a4
    geometry:
      - margin=25mm
    fontsize: 11pt
    colorlinks: true
  docx:
    toc-depth: 2
    highlight-style: github
  typst:
    # pdf also writes ${name}.pdf.
    output-file: ${name}-typst.pdf
    papersize: a4
    margin:
      x: 25mm
      y: 25mm
    fontsize: 11pt
    section-numbering: 1.1.a
---

# Introduction

Quarto renders this one source to HTML, PDF (LaTeX), Word, and Typst.
Render a single format with `quarto render ${name}.qmd --to typst`.

See @knuth84 for the origin of literate programming, and @tbl-formats for
the formats configured above.

::: {.callout-note}
Each format block in the header holds options for that format only.
Options at the top level (`toc`, `number-sections`) apply to every format.
:::

# Formats

| Format | Engine   | Output      |
|--------|----------|-------------|
| html   | Pandoc   | `.html`     |
| pdf    | LaTeX    | `.pdf`      |
| docx   | Pandoc   | `.docx`     |
| typst  | Typst    | `.pdf`      |

: Configured output formats {#tbl-formats}

# References {.unnumbered}

::: {#refs}
:::
