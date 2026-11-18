#!/usr/bin/env python3
"""
verify_relational_mapping.py - Conditional gate: relational storage mappings
(Stage 04a) must satisfy the Rmap rules. Skips features whose storage profile is
not relational (RDF named-graph profiles are unaffected).

Why this exists:
  CLAD's Stage 03b data model maps deterministically to a relational schema via
  Halpin's Rmap. The one CLAD-specific rule the mapping must honour is R2: no
  foreign key crosses a concept boundary. This gate catches a mapping that
  reintroduces cross-concept coupling at the schema level.
"""

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_runner as cr  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent

# A relational storage mapping declares a SQL-ish schema surface. Avoid bare
# `table` (matches "mutable") and `non-relational` / `not relational`.
RELATIONAL_MARKER = re.compile(
    r"(PostgreSQL|Postgres|CREATE\s+TABLE|FOREIGN\s+KEY|\bschema per\b|"
    r"\bR-?map\b|(?<!non-)(?<!not )\brelational\b)",
    re.IGNORECASE)

# Flag a DDL-shaped FK declaration in a Stage 04a mapping. Prose such as
# "intra-concept foreign key" is the expected way to document a derived FK and
# is not a violation; a raw `REFERENCES table(col)` is the shape that can hide a
# cross-concept coupling (R2).
FK_RE = re.compile(
    r"\bFOREIGN\s+KEY\s*\([^)]*\)\s*REFERENCES\b"
    r"|\bREFERENCES\s+[\w.\"]+\s*\(",
    re.IGNORECASE)


def is_relational(text):
    """True when a Stage 04a storage mapping declares a relational profile."""
    return bool(RELATIONAL_MARKER.search(text))


def validate_relational_mapping(text):
    """Return a list of violation strings for a relational storage mapping."""
    failures = []
    for index, line in enumerate(text.splitlines(), 1):
        if FK_RE.search(line):
            failures.append(
                f"line {index}: raw FK declaration in a Stage 04a mapping — "
                f"confirm it is intra-concept; cross-concept FKs are "
                f"forbidden (R2) — {line.strip()}")
    return failures


def storage_mappings_in(storage_dir):
    """Yield (path, text) for every relational *.storage.md in storage_dir."""
    directory = Path(storage_dir)
    if not directory.is_dir():
        return
    for storage_md in sorted(directory.glob("*.storage.md")):
        text = storage_md.read_text(encoding="utf-8")
        if is_relational(text):
            yield storage_md, text


def main(argv=None) -> int:
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--storage-dir", default="", help="Directory of *.storage.md files (defaults to all features)")

    def body(args: argparse.Namespace) -> cr.Verdict:
        if args.storage_dir:
            mappings = list(storage_mappings_in(args.storage_dir))
        else:
            features = REPO_ROOT / "features"
            mappings = []
            if features.is_dir():
                for output_dir in features.glob(
                        "UC-*/stages/04_implement/04a_storage-mapping/output"):
                    mappings.extend(storage_mappings_in(output_dir))

        if not mappings:
            return cr.Verdict.ok("no relational storage mappings to validate")

        failures = []
        for path, text in mappings:
            for failure in validate_relational_mapping(text):
                try:
                    rel = path.relative_to(REPO_ROOT)
                except ValueError:
                    rel = path
                failures.append(f"{rel}: {failure}")

        if failures:
            return cr.Verdict.fail(
                f"{len(failures)} relational mapping violation(s):", [
                    cr.Problem(f) for f in failures])

        return cr.Verdict.ok(
            f"{len(mappings)} relational storage mapping(s) satisfy the Rmap rules")

    return cr.run_check(
        "Validate relational Stage 04a storage mappings.",
        body, argv, configure)


if __name__ == "__main__":
    sys.exit(main())
