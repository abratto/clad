#!/usr/bin/env python3
"""
verify_concept_additivity.py — Model B additive-only gate for corpus concepts.

Why this exists:
  A concept is a canonical, system-scope asset (R22). A feature either
  introduces it (`new`) or **extends** it; an extend is promoted over the
  canonical entry. The convention is *additive only*: a later use case may add
  fact types, constraints, actions and outcomes, but it must not quietly drop
  or restate what an earlier use case established. Without a mechanical check
  that convention is social — `_state_changed` is a DIFFERENCE test, so a
  proposal that removes a state line looks exactly like one that adds a line,
  and promotion copies it over the canonical entry either way.

What it protects (per `extends:*` concept):
  * the concept spec's `## State` lines — every canonical line must survive in
    the proposal (a gained line is fine; a lost or restated line is not);
  * the canonical **contract** — every canonical action must survive, and every
    canonical outcome of a surviving action must still be listed.

A `new` concept has no canonical entry to protect and is skipped, as is a
proposal whose canonical entry does not exist yet.

Deliberate removals:
  Additive-only is the default, not a law. A deliberate removal (a fact type
  genuinely retired, a value type corrected) is authorised by listing the exact
  dropped line in the feature's `_config/additivity-exceptions.md`, one bullet
  per line, with a reason. The check subtracts exactly those lines and still
  fails on anything else — so a removal is visible, reviewed, and bounded.

Usage:
  python3 verify_concept_additivity.py --feature features/UC-XX-<slug> \
      [--corpus features/_system/concepts]

Exit: 0 pass/skip, 1 fail.
"""

import argparse
import os
import re
import sys

import artifact_parsers as ap


EXCEPTION_FILE = os.path.join("_config", "additivity-exceptions.md")


def load_exceptions(feature_root):
    """Exact line(s) the human has authorised dropping, from `_config/`.

    One bullet per authorisation. The backticked spans on the bullet are the
    lines; the rest is the reason and is not parsed.
    """
    path = os.path.join(feature_root, EXCEPTION_FILE)
    allowed = set()
    if not os.path.isfile(path):
        return allowed
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped.startswith(("-", "*")):
                continue
            allowed.update(_normalised(m) for m in re.findall(r"`([^`]+)`", stripped))
    return allowed


def _normalised(line: str) -> str:
    """A state line without its alignment, which is presentation only.

    Canonical state lines are comment-aligned; adding a longer relation name
    re-flows that column. Comparing raw text would read a re-alignment as a
    restatement of every line above it, which is not what "not additive" means.
    """
    return re.sub(r"\s+", " ", line).strip()


def dropped_state_lines(feature_root, corpus, concept):
    """Canonical `## State` lines the proposal no longer carries."""
    canonical = os.path.join(corpus, concept + ".concept.md")
    proposal = os.path.join(feature_root, "stages", "02_concepts", "output",
                            concept + ".concept.md")
    if not os.path.isfile(canonical) or not os.path.isfile(proposal):
        return []
    before = {_normalised(line)
              for line in ap.parse_concept(canonical).state_lines}
    after = {_normalised(line)
             for line in ap.parse_concept(proposal).state_lines}
    return sorted(before - after)


def dropped_contract_terms(feature_root, corpus, concept):
    """Canonical actions and outcomes the proposal's contract no longer carries."""
    contract_dir = os.path.join(feature_root, "stages", "04_implement",
                                "04b_contract", "output")
    before = {(c, a): o for (c, a), o in ap.parse_spec_outcomes(corpus).items()
              if c == concept}
    after = {(c, a): o for (c, a), o in ap.parse_spec_outcomes(contract_dir).items()
             if c == concept}
    if not before or not after:
        return []
    dropped = []
    for (c, action), outcomes in sorted(before.items()):
        if (c, action) not in after:
            dropped.append(f"action `{action}`")
            continue
        for outcome in sorted(outcomes - after[(c, action)]):
            dropped.append(f"outcome `{outcome}` of `{action}`")
    return dropped


def main():
    parser = argparse.ArgumentParser(
        description="Model B additive-only check for extended corpus concepts")
    parser.add_argument("--feature", required=True)
    parser.add_argument("--corpus", default="",
                        help="Canonical corpus dir (default: the feature's)")
    args = parser.parse_args()

    feature_root = os.path.abspath(args.feature)
    resp = os.path.join(feature_root, "stages", "01a_responsibility-map",
                        "output", "responsibility-map.md")
    if not os.path.isfile(resp):
        print("SKIP  no responsibility map — nothing to compare")
        return 0

    corpus = args.corpus or ap._default_corpus_dir(feature_root)
    entries = ap.parse_responsibility_map(resp)
    allowed = load_exceptions(feature_root)

    failures = []
    checked = 0
    for concept, entry in sorted(entries.items()):
        origin = (entry.origin or "").strip().lower()
        if not origin.startswith("extend"):
            continue          # `new` has no canonical entry; `reused` derives nothing
        if not os.path.isfile(os.path.join(corpus, concept + ".concept.md")):
            continue          # canonical not promoted yet — nothing to protect
        checked += 1

        lost = [line for line in dropped_state_lines(feature_root, corpus, concept)
                if line not in allowed]
        if lost:
            failures.append(
                f"{concept}: the proposal drops canonical state "
                f"line(s) the corpus holds — this is not additive:")
            failures.extend(f"  - {line}" for line in lost)

        terms = [t for t in dropped_contract_terms(feature_root, corpus, concept)
                 if t not in allowed]
        if terms:
            failures.append(
                f"{concept}: the proposal's contract drops canonical "
                f"term(s) — this is not additive:")
            failures.extend(f"  - {t}" for t in terms)

    if not checked:
        print("SKIP  no extended concept has a canonical entry yet")
        return 0

    if failures:
        print("FAIL  additive-only violated for a canonical concept")
        for failure in failures:
            print(f"  {failure}")
        print(f"  Authorise a deliberate, bounded removal by listing the exact "
              f"line in {EXCEPTION_FILE}; anything else must be additive.")
        return 1

    note = f" ({len(allowed)} authorised exception(s))" if allowed else ""
    print(f"PASS  additive-only holds across {checked} extended concept(s){note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
