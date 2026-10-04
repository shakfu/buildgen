<%
import json
_author = user.get("name") if user else None
%>\
---
title: "${name}"
% if _author:
author: ${json.dumps(_author)}
% endif
format:
  dashboard:
    theme: cosmo
    orientation: rows
    scrolling: false
    nav-buttons: []
    embed-resources: true
---

${"##"} Row {height=25%}

::: {.valuebox icon="people" color="primary"}
Users

1,024
:::

::: {.valuebox icon="graph-up" color="success"}
Growth

12%
:::

::: {.valuebox icon="exclamation-triangle" color="warning"}
Open issues

7
:::

${"##"} Row {height=75%}

${"###"} Column {width=60%}

::: {.card title="Overview"}
Replace these cards with plots or tables. Add a code cell
(Python, R, or Julia) to compute the values above.
:::

${"###"} Column {width=40%}

::: {.card title="Notes"}
Dashboards render to HTML only.
:::
