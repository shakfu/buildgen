---
title: "${name}"
---

# Overview

This project renders every document with the options in `_quarto.yml`.
The other documents are `analysis.qmd` and `notes/meeting.qmd`.

Literate programming [@knuth84] combines prose and code in one source.

# Rendering

- `quarto render` renders every document to every format.
- `quarto render analysis.qmd --to pdf` renders one document to one format.
- `quarto render notes` renders one directory.
