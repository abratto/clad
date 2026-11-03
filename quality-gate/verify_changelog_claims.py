#!/usr/bin/env python3
"""Guard: the newest CHANGELOG entry matches the newest release tag, and the
repository paths it names exist.

Why this exists:
  0.29.0 shipped a summary that said the committed login migration "remains
  byte-identical" when it had changed (comment-only, but the prose was still
  wrong), and earlier drafts cited a `RmapDeriver` that the same release
  deleted. A release note is a claim about the tree; this check keeps the
  cheapest claims honest without pretending to re-run the release:

  * The newest `## [x.y.z]` heading must equal the newest `vX.Y.Z` git tag
    (when tags exist). A note written ahead of its tag, or a tag whose note was
    never added, is drift.
  * Every backticked token that looks like a repo-relative path (has a `/` and a
    file extension, or ends in `/`) must resolve in the tree. A note that cites
    a file the release removed is a broken promise.

This is advisory by design: it never fails the gate on a prose path that is
merely illustrative (it only checks tokens shaped like real paths).

Usage:
  python3 verify_changelog_claims.py [--root <repo>] [--changelog CHANGELOG.md]

Exit: 0 pass/skip, 1 a version/tag mismatch or a dangling cited path.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_runner as cr  # noqa: E402

VERSION_HEADING = re.compile(r"^##\s*\[(\d+\.\d+\.\d+)\]", re.MULTILINE)
BACKTICK = re.compile(r"`([^`\n]+)`")
# A token shaped like a repo-relative file path: has a slash AND a dotted
# filename. Directory mentions (e.g. a search root that exists only once used)
# are illustrative and are NOT checked — a release note may name a directory the
# release does not create.
PATH_TOKEN = re.compile(r"^[\w./-]*/[\w.-]*\.[A-Za-z0-9]+$")
SKIP_PREFIXES = ("http://", "https://", "./", "../", "~/")
SKIP_SUFFIX_WORDS = {"…", "..."}


def _newest_tag(root: str):
    try:
        out = subprocess.run(
            ["git", "tag", "--sort=-v:refname"], cwd=root,
            capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    for line in out.splitlines():
        line = line.strip()
        if re.fullmatch(r"v\d+\.\d+\.\d+", line):
            return line[1:]
    return None


def _latest_section(text: str) -> str:
    first = VERSION_HEADING.search(text)
    if not first:
        return ""
    rest = text[first.end():]
    nxt = re.search(r"^##\s", rest, re.MULTILINE)
    return rest[:nxt.start()] if nxt else rest


def check(root: str, changelog: str):
    problems = []
    text = open(changelog, encoding="utf-8").read()
    versions = VERSION_HEADING.findall(text)
    if not versions:
        return cr.Verdict.skip("no versioned CHANGELOG heading found")

    newest = versions[0]
    tag = _newest_tag(root)
    if tag is not None and tag != newest:
        problems.append(cr.Problem(
            f"CHANGELOG's newest entry is {newest} but the newest git tag is "
            f"v{tag}", where=os.path.basename(changelog)))

    section = _latest_section(text)
    cited = 0
    for token in BACKTICK.findall(section):
        token = token.strip()
        if not token or token.startswith(SKIP_PREFIXES):
            continue
        if token in SKIP_SUFFIX_WORDS or " " in token:
            continue
        if not PATH_TOKEN.match(token):
            continue
        relative = token.rstrip("/")
        cited += 1
        if not os.path.exists(os.path.join(root, relative)):
            problems.append(cr.Problem(
                f"cites `{token}` but it does not exist in the tree",
                where=f"CHANGELOG {newest}"))

    if problems:
        return cr.Verdict.fail(
            f"{len(problems)} release-note claim(s) drifted from the tree",
            problems)
    return cr.Verdict.ok(
        f"release notes for {newest} match the tag and cite {cited} "
        f"existing path(s)")


def main(argv=None) -> int:
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--root", default=None,
                            help="Repo root (default: parent of this script)")
        parser.add_argument("--changelog", default=None)

    def body(args: argparse.Namespace) -> cr.Verdict:
        root = args.root or os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        root = os.path.abspath(root)
        changelog = args.changelog or os.path.join(root, "CHANGELOG.md")
        if not os.path.isfile(changelog):
            return cr.Verdict.skip("no CHANGELOG.md")
        return check(root, changelog)

    return cr.run_check("Verify release-note claims match the tree",
                        body, argv, configure)


if __name__ == "__main__":
    sys.exit(main())
