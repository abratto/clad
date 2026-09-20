#!/usr/bin/env python3
"""
verify_concept_criteria.py — criteria gate: the mechanical subset of the
concept criteria.

Why this exists:
  A concept is a unit of functionality chunked around one purpose, with an
  operational principle, polymorphic state over a set of individuals, and no
  dependence on other concepts. Most of that is judgment (see the human
  checklist in Stage 02's contract). This script makes the CHECKABLE subset
  deterministic so the judgment checklist is not asked to catch mechanical
  defects (maintenance change `system-scope-concept-vocabulary`, decision D6).

Checks per `<Name>.concept.md`:

  FAIL  operational principle present — a `## Operational principle` section
        whose fenced block is non-empty (the end-to-end witness trace).
  FAIL  no external types — no state or action type is the name of ANOTHER
        concept in the corpus. That is the R1 leak (a concept reaching into a
        neighbour instead of using an opaque id or a type parameter).
  WARN  type parameters declared — the header `concept Name [Params]` should
        declare at least one type parameter (D2).
  WARN  capability naming — the name should denote an ability, not an entity
        noun (advisory; the template's anti-pattern names are `User`, `Post`,
        ...). Jackson's own `Session` is therefore NOT flagged.

Usage:
  python3 verify_concept_criteria.py [--concept-dir features/_system/concepts]
                                     [--advisory]

  Stage 02 passes the feature's proposals plus the canonical corpus, so a
  proposal shadows the corpus spec of the same name:
  python3 verify_concept_criteria.py \
    --concept-dir features/UC-XX-<slug>/stages/02_concepts/output \
    --concept-dir features/_system/concepts

Exit: 0 pass/warn/skip, 1 fail.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifact_parsers as ap  # noqa: E402

OP_SECTION = re.compile(r"^##\s+Operational principle\s*$(.*?)(?=^##\s|\Z)",
                        re.MULTILINE | re.DOTALL)
STATE_SECTION = re.compile(r"^##\s+State\s*$(.*?)(?=^##\s|\Z)",
                           re.MULTILINE | re.DOTALL)
ACTIONS_SECTION = re.compile(r"^##\s+Actions\s*$(.*?)(?=^##\s|\Z)",
                             re.MULTILINE | re.DOTALL)
HEADER = re.compile(r"^concept\s+(\w+)\s*(?:\[([^\]]*)\])?", re.MULTILINE)
WITNESS = re.compile(r"^\s*(after|then)\b", re.MULTILINE)
CAPITALISED = re.compile(r"\b([A-Z][A-Za-z0-9_]*)\b")

# Entity nouns the concept template names as anti-patterns. Advisory only:
# a concept is a capability, not the entity noun its set ranges over.
ANTI_PATTERN_NAMES = {
    "User", "Account", "Profile", "Post", "Article", "Comment",
    "Order", "Item", "Product", "Customer", "Message", "Document",
}


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def check_one(path, others):
    """Return (failures, warnings) for one concept file."""
    name = os.path.basename(path).replace(".concept.md", "")
    text = read(path)
    failures, warnings = [], []

    header = HEADER.search(text)
    type_params = (header.group(2).strip() if header and header.group(2) else "")

    # 1. Operational principle present and non-empty.
    op = OP_SECTION.search(text)
    body = op.group(1) if op else ""
    fenced = re.findall(r"```(.*?)```", body, re.DOTALL)
    if not op or not any(WITNESS.search(block) for block in fenced):
        failures.append(
            "no `## Operational principle` witness trace (a non-empty fenced "
            "`after`/`then` block) — the end-to-end test of the concept")

    # 2. No external types: a state/action type named after another concept.
    leak_section = ""
    for section in (STATE_SECTION.search(text), ACTIONS_SECTION.search(text)):
        if section:
            leak_section += section.group(1)
    used_types = set(CAPITALISED.findall(leak_section))
    leaked = sorted(used_types & (others - {name}))
    if leaked:
        failures.append(
            "external type reference(s) %s — a concept must not name another "
            "concept's type (R1); use an opaque id or a type parameter"
            % ", ".join(leaked))

    # 3. Type parameters declared (advisory).
    if not type_params:
        warnings.append(
            "no type parameters declared in the header (`concept %s [ ... ]`)" % name)

    # 4. Capability naming heuristic (advisory).
    if name in ANTI_PATTERN_NAMES:
        warnings.append(
            "`%s` is an entity noun; name the capability instead (advisory)" % name)

    return failures, warnings


def main():
    parser = argparse.ArgumentParser(
        description="Verify the mechanical subset of the concept criteria")
    parser.add_argument("--concept-dir", action="append", default=None,
                        help="Concept-spec dir; repeatable. Earlier dirs shadow "
                             "later ones by concept name. Defaults to the "
                             "system corpus.")
    parser.add_argument("--advisory", action="store_true",
                        help="Report failures as warnings (exit 0)")
    args = parser.parse_args()

    dirs = args.concept_dir or ["features/_system/concepts"]
    specs = ap.concept_spec_paths(dirs)
    if not specs:
        print("SKIP  no concept specs under %s" % ", ".join(dirs))
        return 0

    names = set(specs)
    all_failures, all_warnings = [], []
    for name, path in sorted(specs.items()):
        failures, warnings = check_one(path, names)
        all_failures.extend("%s: %s" % (name, f) for f in failures)
        all_warnings.extend("%s: %s" % (name, w) for w in warnings)

    for warning in all_warnings:
        print("WARN  %s" % warning)

    if all_failures:
        label = "WARN" if args.advisory else "FAIL"
        print("%s  %d concept criteria failure(s):" % (label, len(all_failures)))
        for failure in all_failures:
            print("  - %s" % failure)
        return 0 if args.advisory else 1

    print("PASS  %d concept(s) satisfy the mechanical criteria (%d warning(s))"
          % (len(specs), len(all_warnings)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
