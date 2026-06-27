#!/usr/bin/env python3
"""Update GitHub Actions pins in workflow files to their latest releases.

Scans this repo's real workflows (``.github/workflows``) and the generated-project
workflow templates (``src/buildgen/templates/**/github-workflows``) for
``uses: owner/repo@ref`` lines, looks up each action's latest release via the
GitHub API, and rewrites the ref.

Convention: refs are normalized to a major-version tag (``@v8``) so every
reference to a given action stays consistent and tracks the latest major. Use
``--style full`` for exact tags (``@v8.2.0``) instead.

Examples::

    python scripts/update_workflow_actions.py            # dry run, show changes
    python scripts/update_workflow_actions.py --write     # apply changes
    python scripts/update_workflow_actions.py --style full --write

Auth: prefers the ``gh`` CLI (uses its stored credentials). Falls back to a
plain HTTPS request to api.github.com, honoring ``GITHUB_TOKEN`` if set to avoid
the low unauthenticated rate limit.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# owner/repo@ref. ref may contain '/' (e.g. branch refs like release/v1), so it
# is matched greedily up to whitespace; should_update() decides what to rewrite.
USES_RE = re.compile(
    r"(?P<prefix>uses:\s*)(?P<action>[\w.-]+/[\w.-]+)@(?P<ref>[\w./-]+)"
)

# A ref we are willing to bump: a version tag (v8, v8.2.0, 8.2) or a commit SHA.
# Branch/floating refs (release/v1, main, master) are intentionally left alone.
VERSION_TAG_RE = re.compile(r"^v?\d+(\.\d+)*$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def should_update(ref: str) -> bool:
    return bool(VERSION_TAG_RE.match(ref) or SHA_RE.match(ref))

# Directories scanned, relative to the repo root. Both literal workflows and
# the .mako templates that generate downstream workflows.
SCAN_GLOBS = (
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    "src/buildgen/templates/**/github-workflows/*",
)


@dataclass(frozen=True)
class Change:
    path: Path
    action: str
    old_ref: str
    new_ref: str

    @property
    def changed(self) -> bool:
        return self.old_ref != self.new_ref


def repo_root() -> Path:
    """Repo root: the git toplevel, falling back to this script's parent."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path(__file__).resolve().parent.parent


def discover_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in SCAN_GLOBS:
        files.update(p for p in root.glob(pattern) if p.is_file())
    return sorted(files)


def fetch_latest_tag_gh(action: str) -> str | None:
    try:
        out = subprocess.run(
            ["gh", "api", f"repos/{action}/releases/latest", "--jq", ".tag_name"],
            capture_output=True,
            text=True,
            check=True,
        )
        tag = out.stdout.strip()
        return tag or None
    except subprocess.CalledProcessError:
        return None


def fetch_latest_tag_http(action: str) -> str | None:
    url = f"https://api.github.com/repos/{action}/releases/latest"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        return data.get("tag_name") or None
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"  warning: HTTP lookup for {action} failed: {exc}", file=sys.stderr)
        return None


def make_resolver(use_gh: bool):
    """Return a cached latest-tag resolver."""
    cache: dict[str, str | None] = {}
    fetch = fetch_latest_tag_gh if use_gh else fetch_latest_tag_http

    def resolve(action: str) -> str | None:
        if action not in cache:
            cache[action] = fetch(action)
        return cache[action]

    return resolve


def desired_ref(tag: str, style: str) -> str | None:
    """Map a release tag (e.g. ``v8.2.0``) to the desired ref for ``style``."""
    if style == "full":
        return tag
    # style == "major": take the leading vN component.
    m = re.match(r"v?(\d+)", tag)
    if not m:
        return None
    return f"v{m.group(1)}"


def plan_changes(files: list[Path], resolve, style: str) -> list[Change]:
    changes: list[Change] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for m in USES_RE.finditer(text):
            action, ref = m.group("action"), m.group("ref")
            if not should_update(ref):
                continue  # leave branch/floating refs (release/v1, main) alone
            tag = resolve(action)
            if tag is None:
                changes.append(Change(path, action, ref, ref))  # unresolved -> no-op
                continue
            new_ref = desired_ref(tag, style)
            if new_ref is None:
                continue
            changes.append(Change(path, action, ref, new_ref))
    return changes


def apply_changes(files: list[Path], resolve, style: str) -> int:
    applied = 0
    for path in files:
        text = path.read_text(encoding="utf-8")

        def repl(m: re.Match) -> str:
            nonlocal applied
            action, ref = m.group("action"), m.group("ref")
            if not should_update(ref):
                return m.group(0)
            tag = resolve(action)
            if tag is None:
                return m.group(0)
            new_ref = desired_ref(tag, style)
            if new_ref is None or new_ref == ref:
                return m.group(0)
            applied += 1
            return f"{m.group('prefix')}{action}@{new_ref}"

        new_text = USES_RE.sub(repl, text)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
    return applied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="apply changes (default: dry run, show what would change)",
    )
    parser.add_argument(
        "--style",
        choices=("major", "full"),
        default="major",
        help="pin to major tag (vN, default) or full release tag (vN.N.N)",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    files = discover_files(root)
    if not files:
        print("No workflow files found.", file=sys.stderr)
        return 1

    use_gh = shutil.which("gh") is not None
    if not use_gh:
        print("gh CLI not found; falling back to api.github.com.", file=sys.stderr)
    resolve = make_resolver(use_gh)

    changes = plan_changes(files, resolve, args.style)

    unresolved = sorted({c.action for c in changes if resolve(c.action) is None})
    if unresolved:
        for action in unresolved:
            print(f"warning: could not resolve latest release for {action}", file=sys.stderr)

    updates = [c for c in changes if c.changed]
    if not updates:
        print("All actions already at their latest %s version." % args.style)
        return 0

    # Report grouped by action so consistency is easy to eyeball.
    print(f"{'APPLYING' if args.write else 'DRY RUN'} (style={args.style}):\n")
    by_action: dict[str, list[Change]] = {}
    for c in updates:
        by_action.setdefault(c.action, []).append(c)
    for action in sorted(by_action):
        refs = by_action[action]
        olds = sorted({c.old_ref for c in refs})
        new = refs[0].new_ref
        rel = ", ".join(sorted({str(c.path.relative_to(root)) for c in refs}))
        print(f"  {action}: {', '.join(olds)} -> {new}")
        print(f"      in: {rel}")

    if not args.write:
        print("\nRe-run with --write to apply.")
        return 0

    applied = apply_changes(files, resolve, args.style)
    print(f"\nApplied {applied} update(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
