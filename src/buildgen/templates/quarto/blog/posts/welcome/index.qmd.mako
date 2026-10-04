<%
import json
from datetime import date
_author = user.get("name") if user else None
%>\
---
title: "Welcome"
description: "The first post"
% if _author:
author: ${json.dumps(_author)}
% endif
date: "${date.today().isoformat()}"
categories: [news]
---

This is the first post in a Quarto blog. Welcome!
