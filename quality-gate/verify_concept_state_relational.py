#!/usr/bin/env python3
"""
verify_concept_state_relational.py — Stage 02 gate: concept state must be
relations over a set of individuals, not a single object's instance variables.

Why this exists:
    Daniel Jackson's "Why concepts aren't objects" identifies the canonical
    mistake agents make when authoring concepts: writing the State block as a
    list of a *single individual's* fields (e.g. `userid, username, password,
    email`) instead of as relations over a *set* of individuals
    (`username: UserId -> String`). The former hides the scope problem — the
    action "which user?" is swept under the rug — and is the object-oriented
    trap the essay warns against.

    This script makes that smell deterministic. It also flags the second
    signature of the trap: a relation whose subject type is the concept's own
    name (the concept models one row per instance instead of owning the set).

Checks (per <Name>.concept.md):
    1. A ## State section exists and is a fenced block.
    2. Every state field uses relational notation `field: Subject -> Type`.
       A bare field name (no `->`) is the object-smell.
    3. No state field uses the concept's own name as its subject type
       (that is "one object", not "a set of individuals").

Stateless concepts are exempt: the line `*None.* <Name> is stateless.`
short-circuits the field checks.

Usage:
  python3 verify_concept_state_relational.py --concept-dir <02_concepts/output/>
"""

import argparse
import os
import re
import sys


# The stateless marker from templates/concept.md.
STATELESS_RE = re.compile(r"\*None\.\*\s+\w+\s+is stateless\.", re.IGNORECASE)
# A relational state field:  field: SubjectType -> FieldType  [-- multiplicity]
FIELD_RE = re.compile(r"^\s*(\w+)\s*:\s*([\w<>, ]+?)\s*->\s*(\w+)")
# The concept header: concept Name [TypeParams]
HEADER_RE = re.compile(r"^\s*concept\s+(\w+)")


def check_concept(path):
    """Return a list of failure strings for one concept file."""
    failures = []
    name = os.path.basename(path)
    with open(path, encoding="utf-8") as fh:
        content = fh.read()

    m = HEADER_RE.search(content)
    if not m:
        failures.append("no `concept <Name>` header found")
        return failures
    concept_name = m.group(1)

    # Locate the ## State section and its fenced block.
    lines = content.split("\n")
    state_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^##\s+State\s*$", line.strip()):
            state_idx = i
            break
    if state_idx is None:
        failures.append("missing `## State` section")
        return failures

    fence_start = None
    for i in range(state_idx, len(lines)):
        if lines[i].strip().startswith("```"):
            fence_start = i
            break
    if fence_start is None:
        failures.append("`## State` section has no fenced code block")
        return failures

    fence_end = None
    for i in range(fence_start + 1, len(lines)):
        if lines[i].strip().startswith("```"):
            fence_end = i
            break
    if fence_end is None:
        failures.append("`## State` code block is not closed")
        return failures

    body = lines[fence_start + 1:fence_end]

    # Stateless concepts are exempt.
    if any(STATELESS_RE.search(line) for line in body):
        return failures

    for raw in body:
        line = raw.strip()
        if not line or line.startswith(">"):
            continue
        # Skip the relational-notation guidance comment lines that some
        # files copy in verbatim (they contain "->" and would pass FIELD_RE,
        # but guidance prose like "field: SubjectType -> FieldType -- mandatory"
        # uses backticks; be conservative and skip pure-prose lines without a
        # leading field token).
        if line.startswith("`") or line.startswith("!"):
            continue

        m = FIELD_RE.match(line)
        if m:
            subject = m.group(2).strip()
            # Check 3: subject type must not be the concept's own name.
            if subject == concept_name:
                failures.append(
                    f"state field '{line}' uses the concept's own name as its "
                    f"subject type — this models one object, not a set of "
                    f"individuals. Use an identifier type (e.g. {concept_name}Id), "
                    f"not '{concept_name}'.")
            continue

        # Check 2: a non-relational field line (the object-smell).
        # A line is a candidate field if it looks like `name: Type` or a bare
        # `name`, but has no `->`.
        if re.match(r"^\w+(\s*:|,)", line) or re.match(r"^\w+\s*$", line):
            failures.append(
                f"state line '{line}' is not relational notation "
                f"(`field: SubjectType -> FieldType`). A bare field list is the "
                f"object-oriented trap — declare the set it ranges over.")

    return failures


def main():
    parser = argparse.ArgumentParser(
        description="Validate concept state uses relational set notation")
    parser.add_argument("--concept-dir", required=True,
                        help="Path to 02_concepts/output/")
    args = parser.parse_args()

    concept_dir = args.concept_dir
    if not os.path.isdir(concept_dir):
        print(f"FAIL  concept directory not found: {concept_dir}")
        sys.exit(1)

    files = sorted(f for f in os.listdir(concept_dir)
                   if f.endswith(".concept.md"))
    if not files:
        print("FAIL  no .concept.md files found")
        sys.exit(1)

    total = 0
    for fname in files:
        for msg in check_concept(os.path.join(concept_dir, fname)):
            print(f"FAIL  {fname}: {msg}")
            total += 1

    if total == 0:
        print(f"PASS  {len(files)} concept(s) use relational state notation")
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
