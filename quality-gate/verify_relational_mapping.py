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
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent

# A relational storage mapping declares a SQL-ish schema surface.
RELATIONAL_MARKER = re.compile(
    r"(PostgreSQL|Postgres|relational|CREATE TABLE|schema per|table)", re.IGNORECASE)

# Any FK declaration in a CLAD mapping is a cross-concept coupling (concepts own
# isolated regions; cross-concept identifiers are opaque, never references).
FK_RE = re.compile(r"\b(REFERENCES|FOREIGN KEY)\b", re.IGNORECASE)


def is_relational(text):
    """True when a Stage 04a storage mapping declares a relational profile."""
    return bool(RELATIONAL_MARKER.search(text))


def validate_relational_mapping(text):
    """Return a list of violation strings for a relational storage mapping."""
    failures = []
    for index, line in enumerate(text.splitlines(), 1):
        if FK_RE.search(line):
            failures.append(
                f"line {index}: cross-concept foreign key is forbidden "
                f"(R2) — {line.strip()}")
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


def main():
    parser = argparse.ArgumentParser(description="Validate relational Stage 04a storage mappings.")
    parser.add_argument("--storage-dir", default="", help="Directory of *.storage.md files (defaults to all features)")
    args = parser.parse_args()

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
        print("PASS  no relational storage mappings to validate")
        return

    failures = []
    for path, text in mappings:
        for failure in validate_relational_mapping(text):
            try:
                rel = path.relative_to(REPO_ROOT)
            except ValueError:
                rel = path
            failures.append(f"{rel}: {failure}")

    if failures:
        print(f"FAIL: {len(failures)} relational mapping violation(s):")
        for failure in failures:
            print(f"  {failure}")
        sys.exit(1)

    print(f"PASS  {len(mappings)} relational storage mapping(s) satisfy the Rmap rules")


if __name__ == "__main__":
    main()
