#!/usr/bin/env python3
"""
verify_code_refs.py — advisory: backticked code references resolve.

Why this exists:
  Docs cite code (`SyncEngine.java`, `quality-gate/generate_syncs.py:168`,
  `artifact_parsers.py#sync_stem`). A rename or a refactor leaves the citation
  pointing at nothing, and nothing notices — the reader trusts a stale path.
  This is the companion to `verify_mechanism_citations.py`: that check forces a
  citation to exist; this one keeps it honest.

Advisory (exit 0 always): a `file.java:LINE` out of range, or a `.java`/`.py`
token that resolves to no file in the repo, prints a WARN. A path that resolves
by basename but not by the written path is accepted (docs often elide the dir).

Usage:
  python3 verify_code_refs.py --dirs methodology maintenance templates

Exit: always 0 (advisory).
"""

import argparse
import os
import re
import sys

# A backticked `path/File.java`, optionally with `:LINE` or `#symbol`.
REF = re.compile(r"`([\w./-]+\.(?:java|py|kt|scala|ts|js))(?::(\d+)|#[\w.]+)?`")
SKIP_DIRS = {".git", "node_modules", "target", "__pycache__", "scratch",
             ".venv", "dist", "build"}


def repo_index(root):
    """basename -> [paths] for every code file, for basename fallback."""
    index = {}
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name.endswith((".java", ".py", ".kt", ".scala", ".ts", ".js")):
                index.setdefault(name, []).append(os.path.join(dirpath, name))
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description="Advisory code-reference check")
    parser.add_argument("--root", default=".")
    parser.add_argument("--dirs", nargs="+",
                        default=["methodology", "maintenance", "templates"])
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    index = repo_index(root)
    warnings = []
    checked = 0

    for rel in args.dirs:
        base = os.path.join(root, rel)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, files in os.walk(base):
            for name in sorted(files):
                if not name.endswith(".md"):
                    continue
                path = os.path.join(dirpath, name)
                with open(path, encoding="utf-8", errors="replace") as handle:
                    text = handle.read()
                for match in REF.finditer(text):
                    ref, line = match.group(1), match.group(2)
                    # A bare filename with no line is usually an illustrative
                    # example (`UserConcept.java`); only a path-qualified ref or
                    # a `file:LINE` is a concrete citation worth checking.
                    if line is None and "/" not in ref:
                        continue
                    if "<" in ref or ">" in ref:
                        continue
                    checked += 1
                    resolved = os.path.join(root, ref)
                    if not os.path.isfile(resolved):
                        candidates = index.get(os.path.basename(ref), [])
                        if not candidates:
                            warnings.append(
                                f"{os.path.relpath(path, root)}: `{ref}` "
                                f"resolves to no file in the repo")
                            continue
                        resolved = candidates[0]
                    if line is not None:
                        with open(resolved, encoding="utf-8",
                                  errors="replace") as handle:
                            count = sum(1 for _ in handle)
                        if int(line) > count:
                            warnings.append(
                                f"{os.path.relpath(path, root)}: `{ref}:{line}` "
                                f"is past the end of the file ({count} lines)")

    for warning in warnings:
        print(f"WARN  {warning}")
    if warnings:
        print(f"WARN  code references: {len(warnings)} of {checked} do not "
              f"resolve")
    else:
        print(f"PASS  code references: {checked} backticked reference(s) resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
