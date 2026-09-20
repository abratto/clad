#!/usr/bin/env python3
"""
verify_test_continuity.py — Stage gate: red-stage test files unchanged.

Why this exists:
  The outer red loop is mechanically immutable (Gate 3 content hash), but
  the inner TDD loop ("do not redesign the approved red tests") was by
  contract only: a green-stage agent could modify a red-stage test file and
  nothing would detect it. Contract T2 routes any needed red-test change
  through the owning red stage as an R17 re-entry; this script makes T2
  mechanical.

Mechanism:
  The red stage's derivation map (04d-red `concept-test-derivation.md` /
  04e-red `sync-test-derivation.md`) must carry a

      ## Test file continuity

  section: a table of repo-root-relative test-file paths with the SHA-256
  of every produced test file, computed by the agent right after the red
  run. The green stage recomputes the hashes; any drift (content changed)
  or a missing file fails the stage.

Skip-when-absent convention:
  When the derivation map is absent, or the map has no
  `## Test file continuity` section, the check SKIPs (exit 0) — features
  predating this change and non-code changes advance without retrofit.

Usage:
  python3 verify_test_continuity.py \
    --derivation <derivation-map.md> \
    --test-source-root <app/src/test/java>
"""

import argparse
import hashlib
import os
import re
import sys


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_continuity_rows(map_path: str):
    """Return a list of (relative_path, sha256) rows from the map's
    `## Test file continuity` table, or None when the section is absent."""
    if not os.path.isfile(map_path):
        return None
    with open(map_path, encoding="utf-8") as fh:
        text = fh.read()
    m = re.search(r"^#{2}[^\n]*Test file continuity[^\n]*$", text, re.M)
    if not m:
        return None
    section = text[m.end():]
    # stop at the next same-or-higher heading, if any
    nxt = re.search(r"^#{1,2} [^\n]*$", section[1:], re.M)
    if nxt:
        section = section[:nxt.start() + 1]
    rows: list = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [c.strip().strip("`") for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        rel, digest = cells[0], cells[1]
        if not rel or rel.lower().startswith("file path"):
            continue  # header row
        if not re.fullmatch(r"[0-9a-fA-F]{64}", digest or ""):
            continue  # not a continuity row (e.g. example row in template)
        rows.append((rel, digest.lower()))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Red-stage test files must be unchanged since red")
    parser.add_argument("--derivation", required=True,
                        help="path to the red stage's derivation map")
    parser.add_argument("--test-source-root", required=True,
                        help="repo-root-relative (resolved from cwd) test "
                             "source root the paths in the map resolve "
                             "against")
    args = parser.parse_args()

    rows = parse_continuity_rows(args.derivation)
    if rows is None or not rows:
        print("SKIP  test continuity: no '# Test file continuity' section "
              "in the derivation map (feature predates the check)")
        return 0

    drifted: list = []
    missing: list = []
    for rel, digest in rows:
        path = rel if os.path.isabs(rel) else (
            os.path.join(args.test_source_root, rel)
            if not rel.startswith("..") else os.path.normpath(
                os.path.join(args.test_source_root, rel)))
        path = os.path.normpath(path)
        if not os.path.isfile(path):
            missing.append(f"{rel}  (resolved to {path})")
            continue
        if sha256_of(path) != digest:
            drifted.append(rel)

    failures = [f"drifted: {rel}" for rel in drifted] + \
               [f"missing: {rel}" for rel in missing]
    if failures:
        print(f"FAIL  test continuity: {len(failures)} test file(s) changed "
              f"since the red receipt")
        for f in failures:
            print(f"      {f}")
        print(f"      Derivation-map paths are relative to `test.source.root` "
              f"= {args.test_source_root} — the TEST SOURCE ROOT that contains "
              f"package directories (e.g. `app/src/test/java`), not a package "
              f"directory itself.")
        print("      Route the change through the owning red stage "
              "(04d-red/04e-red) as an R17 re-entry — never edit red "
              "tests from the green stage.")
        return 1

    print(f"PASS  test continuity: {len(rows)} test file(s) unchanged since "
          f"red")
    return 0


if __name__ == "__main__":
    sys.exit(main())
