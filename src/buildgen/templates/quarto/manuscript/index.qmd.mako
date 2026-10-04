<%
import json
_author = user.get("name") if user else None
_email = user.get("email") if user else None
%>\
---
title: "${name}"
% if _author:
authors:
  - name: ${json.dumps(_author)}
% if _email:
    email: ${json.dumps(_email)}
% endif
    affiliations:
      - name: Affiliation
    corresponding: true
% endif
date: last-modified
abstract: |
  One-paragraph summary of the article.
keywords:
  - keyword
bibliography: references.bib
number-sections: true
---

${"##"} Introduction

This is a placeholder for the manuscript's main document [@knuth84].

${"##"} Methods

${"##"} Results

${"##"} Discussion
