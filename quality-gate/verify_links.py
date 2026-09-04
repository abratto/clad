#!/usr/bin/env python3
"""
verify_links.py — Validate cross-reference links in CLAD layer-0/3 docs.

Scans the stable documentation surface that AGENTS.md and each stage
CONTEXT.md route agents through — AGENTS.md, CONTEXT.md, methodology/,
templates/, skills/, and the statement docs — and verifies that every
relative-file markdown link resolves to an existing target. This catches
the exact class of drift where a doc cross-references an artefact that a
later iterative change renamed (e.g. User.concept.md -> UserNaming.concept.md).

Only local, relative markdown links `[...](path)` are checked. HTTP links,
bare `#anchor`-only links, and angle-bracket `<...>` autolinks are skipped.
Anchor fragments (`#foo`) are not resolved — this checks file existence.

Skipped by construction:
  - `features/UC-*/stages/*/output/**` (feature outputs change per-feature)
  - `CHANGELOG.md`, `maintenance/**` (historical records)

Usage:
  python3 quality-gate/verify_links.py [--root <repo root>]

Exits 0 if all checked links resolve, 1 otherwise.
"""

import argparse
import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"\]\(\s*([^)]+?)\s*\)")
FENCE_RE = re.compile(r"^\s*(```|~~~)", re.MULTILINE)
TRACKED_DIRS = ("methodology", "templates", "skills")
TRACKED_FILES = ("AGENTS.md", "CONTEXT.md", "CLAUDE.md")
IGNORED_PATH_PARTS = ("/output/", "CHANGELOG.md", "/maintenance/", "/.git/")


def _skip(path):
    s = str(path)
    return any(part in s for part in IGNORED_PATH_PARTS)


def _tracked_md_files(root):
    files = [root / f for f in TRACKED_FILES]
    for d in TRACKED_DIRS:
        files.extend(root.joinpath(d).rglob("*.md"))
    return [f for f in files if f.is_file() and not _skip(f)]


def _strip_fences(text):
    """Blank out fenced code blocks so inline ``(name, ident)`` in
    Mermaid/text examples are not misread as links."""
    out = []
    in_fence = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append("")  # drop the fence line itself
            continue
        out.append("" if in_fence else line)
    return "\n".join(out)


def _resolve(link, source, root):
    # Returns root (a sentinel meaning "non-file link, always ok") or a
    # resolved filesystem Path that must exist.
    if link.startswith(("<", "#")) or link.startswith(("http://", "https://", "mailto:")):
        return root
    path_part = link.split("#", 1)[0].strip()
    if not path_part:
        return root
    base = source.parent if not path_part.startswith("/") else root
    return (base / path_part).resolve()


def main():
    parser = argparse.ArgumentParser(description="Validate CLAD doc cross-reference links")
    parser.add_argument("--root", default=None, help="Repo root (default: parent of this script)")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    if not (root / "AGENTS.md").is_file():
        print(f"FAIL  not a CLAD repo root: {root}")
        sys.exit(1)

    broken = []
    scanned = 0
    for src in _tracked_md_files(root):
        text = _strip_fences(src.read_text(encoding="utf-8", errors="replace"))
        for m in LINK_RE.finditer(text):
            scanned += 1
            target = _resolve(m.group(1).strip(), src, root)
            if target == root:  # non-file link (http/anchor)
                continue
            if not target.exists():
                rel = src.relative_to(root)
                broken.append((src, m.group(1).strip()))

    if broken:
        print(f"FAIL  {len(broken)} broken cross-reference link(s) in CLAD docs")
        for src, link in broken:
            print(f"  {src.relative_to(root)} -> {link}")
        sys.exit(1)

    print(f"PASS  {scanned} cross-reference link(s) checked, {len(_tracked_md_files(root))} docs scanned")
    sys.exit(0)


if __name__ == "__main__":
    main()
