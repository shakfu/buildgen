<%
from datetime import datetime
today = datetime.now().strftime("%Y-%m-%d")
# Mako treats a line-leading "##" as a comment, so emit Markdown headings via vars.
h2 = "##"
h3 = "###"
_opts = context.get("options") or {}
_pure = bool(_opts.get("pure_python", False))
_backend = "hatchling" if _pure else "scikit-build-core"
%>\
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

${h2} [Unreleased]

${h2} [0.1.0] - ${today}

${h3} Added

- Initial project structure
- Core module with example functions
- Test suite with pytest
- Build system using ${_backend}
