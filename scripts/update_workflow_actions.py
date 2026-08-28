#!/usr/bin/env python3
"""Update GitHub Actions pins in workflow files to their latest releases.

Scans this repo's real workflows (``.github/workflows``) for ``uses: owner/repo@ref``
lines and the ``ACTIONS`` table in ``src/buildgen/common/versions.py``, which is
what the generated-project workflow templates render their refs from. Looks up
each action's latest release via the GitHub API and rewrites the ref.

Convention: refs are normalized to the shortest *floating* tag an action
actually publishes, so a reference tracks upstream patch releases without
needing another sweep here. For a latest release of ``v8.2.0`` the candidates
are tried in order ``v8``, ``v8.2``, ``v8.2.0`` and the first one that exists
upstream wins. Not every action publishes moving major tags -- ``pypa/cibuildwheel``
stops at ``v4.2`` and ``astral-sh/setup-uv`` dropped them entirely after v7 --
and writing a ref that does not exist breaks every workflow that uses it, at
action-resolution time, before any job runs. Use ``--style full`` to pin exact
release tags (``v8.2.0``) unconditionally.

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


# The generated-project workflow templates no longer carry literal refs; they
# render them from buildgen.common.versions.ACTIONS, so that table is scanned
# and rewritten like a workflow file.
REGISTRY_REL = "src/buildgen/common/versions.py"

# An ACTIONS entry: `    "owner/repo": "v7",`
REGISTRY_RE = re.compile(
    r'(?P<prefix>^\s*")(?P<action>[\w.-]+/[\w.-]+)(?P<mid>":\s*")(?P<ref>[\w./-]+)"',
    re.MULTILINE,
)

# Paths scanned, relative to the repo root. This repo's own workflows, plus the
# registry that feeds the generated ones. The template glob is kept so a
# hand-written ref in a custom template is still caught.
SCAN_GLOBS = (
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    "src/buildgen/templates/**/github-workflows/*",
    REGISTRY_REL,
)


def pin_re(path: Path) -> re.Pattern[str]:
    """The pin pattern for *path*: registry entries, or `uses:` lines."""
    return REGISTRY_RE if path.name == "versions.py" else USES_RE


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


def tag_exists_gh(action: str, tag: str) -> bool:
    try:
        subprocess.run(
            ["gh", "api", f"repos/{action}/git/ref/tags/{tag}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def tag_exists_http(action: str, tag: str) -> bool:
    url = f"https://api.github.com/repos/{action}/git/ref/tags/{tag}"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return 200 <= resp.status < 300
    except urllib.error.HTTPError:
        return False
    except urllib.error.URLError as exc:
        print(f"  warning: HTTP lookup for {action}@{tag} failed: {exc}", file=sys.stderr)
        return False


def ref_candidates(tag: str, style: str) -> list[str]:
    """Refs to try for a release ``tag``, shortest (most floating) first.

    ``v8.2.0`` yields ``["v8", "v8.2", "v8.2.0"]`` under the default style, and
    just ``["v8.2.0"]`` under ``full``. A tag with a pre-release suffix or any
    other non-numeric shape only ever yields itself.
    """
    if style == "full":
        return [tag]
    m = re.fullmatch(r"v?(\d+)(?:\.(\d+))?(?:\.(\d+))?", tag)
    if m is None:
        return [tag]
    parts = [p for p in m.groups() if p is not None]
    candidates = ["v" + ".".join(parts[: i + 1]) for i in range(len(parts))]
    # The release tag itself is authoritative; keep it as the final fallback
    # even when its spelling differs from the reconstructed one (e.g. "8.2.0").
    if tag not in candidates:
        candidates.append(tag)
    return candidates


class Resolver:
    """Caches latest-release lookups and tag-existence checks per action."""

    def __init__(self, use_gh: bool) -> None:
        self._fetch = fetch_latest_tag_gh if use_gh else fetch_latest_tag_http
        self._exists = tag_exists_gh if use_gh else tag_exists_http
        self._latest_cache: dict[str, str | None] = {}
        self._exists_cache: dict[tuple[str, str], bool] = {}
        self._desired_cache: dict[tuple[str, str], str | None] = {}

    def latest_tag(self, action: str) -> str | None:
        if action not in self._latest_cache:
            self._latest_cache[action] = self._fetch(action)
        return self._latest_cache[action]

    def tag_exists(self, action: str, tag: str) -> bool:
        key = (action, tag)
        if key not in self._exists_cache:
            self._exists_cache[key] = self._exists(action, tag)
        return self._exists_cache[key]

    def desired_ref(self, action: str, style: str) -> str | None:
        """Shortest published ref for ``action``, or None if unresolvable.

        Never returns a ref that does not exist upstream: a workflow pinned to a
        missing tag fails to resolve and takes every job in the file with it.
        """
        key = (action, style)
        if key in self._desired_cache:
            return self._desired_cache[key]

        tag = self.latest_tag(action)
        result: str | None = None
        if tag is not None:
            candidates = ref_candidates(tag, style)
            result = next(
                (c for c in candidates if self.tag_exists(action, c)),
                None,
            )
            if result is None:
                print(
                    f"warning: none of {', '.join(candidates)} exist for {action}; "
                    "leaving its pin alone",
                    file=sys.stderr,
                )
        self._desired_cache[key] = result
        return result


def plan_changes(files: list[Path], resolver: Resolver, style: str) -> list[Change]:
    changes: list[Change] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for m in pin_re(path).finditer(text):
            action, ref = m.group("action"), m.group("ref")
            if not should_update(ref):
                continue  # leave branch/floating refs (release/v1, main) alone
            new_ref = resolver.desired_ref(action, style)
            if new_ref is None:
                changes.append(Change(path, action, ref, ref))  # unresolved -> no-op
                continue
            changes.append(Change(path, action, ref, new_ref))
    return changes


def apply_changes(files: list[Path], resolver: Resolver, style: str) -> int:
    applied = 0
    for path in files:
        text = path.read_text(encoding="utf-8")

        def repl(m: re.Match) -> str:
            """Replace only the ref span, so both pin shapes share one path."""
            nonlocal applied
            action, ref = m.group("action"), m.group("ref")
            if not should_update(ref):
                return m.group(0)
            new_ref = resolver.desired_ref(action, style)
            if new_ref is None or new_ref == ref:
                return m.group(0)
            applied += 1
            start, end = m.span("ref")
            return m.group(0)[: start - m.start()] + new_ref + m.group(0)[end - m.start() :]

        new_text = pin_re(path).sub(repl, text)
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
        help="pin to the shortest published tag (default) or the full release tag",
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
    resolver = Resolver(use_gh)

    changes = plan_changes(files, resolver, args.style)

    unresolved = sorted(
        {c.action for c in changes if resolver.desired_ref(c.action, args.style) is None}
    )
    if unresolved:
        for action in unresolved:
            print(f"warning: could not resolve a usable ref for {action}", file=sys.stderr)

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

    applied = apply_changes(files, resolver, args.style)
    print(f"\nApplied {applied} update(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
