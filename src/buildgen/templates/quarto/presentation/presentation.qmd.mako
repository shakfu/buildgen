<%
import json
_author = user.get("name") if user else None
%>\
---
title: "${name}"
subtitle: "Subtitle"
% if _author:
author: ${json.dumps(_author)}
% endif
date: today
format:
  revealjs:
    theme: simple
    slide-number: true
    transition: slide
    footer: "${name}"
    embed-resources: true
  beamer:
    theme: Madrid
    aspectratio: 169
    navigation: horizontal
    section-titles: true
  pptx:
    slide-level: 2
---

# Section

${"##"} Bullets

::: {.incremental}
- One idea per slide
- Short bullets
- Reveal them one at a time
:::

::: {.notes}
Speaker notes: shown in the reveal.js speaker view (press S), the
PowerPoint notes pane, and Beamer notes pages.
:::

${"##"} Two columns

:::: {.columns}

::: {.column width="50%"}
Left column
:::

::: {.column width="50%"}
Right column
:::

::::

# Summary

${"##"} Next steps

- Edit `${name}.qmd`
- Render one format: `quarto render ${name}.qmd --to revealjs`
