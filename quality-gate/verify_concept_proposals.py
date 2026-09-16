#!/usr/bin/env python3
"""
verify_concept_proposals.py — Stage 02 gate: the proposal set corresponds
exactly to the responsibility map's NEW/EXTEND rows.

Why this exists:
  Concepts are system-scope, canonical assets (maintenance change
  `system-scope-concept-vocabulary`, decisions D2/D5). A feature either BINDS
  to a canonical concept (Origin `reused:UC-XX` — no spec file in its own
  output) or PROPOSES an addition (`new` / `extends:UC-XX` — a
  `<Name>.concept.md` proposal in its output, promoted on gate approval). The
  file manifest only checks presence; this check makes the *relationship*
  explicit and diagnosable, so a REUSE that quietly re-authored a spec (the
  drift this whole change exists to prevent) fails loudly.

Checks (per feature):
  * Every `new` / `extends:UC-XX` row has a `<Name>.concept.md` proposal in
    `02_concepts/output/`.
  * Every proposal in `02_concepts/output/` is a `new` / `extends:UC-XX` row
    in the responsibility map (a `reused` row must not carry a spec file).
  * Every `Origin` value is one of `new`, `reused[:...]`, `extends[:...]`.

A responsibility map with no Origin column (pre-Model-B) is skipped.

Usage:
  python3 verify_concept_proposals.py --feature features/UC-XX-<slug>

Exit: 0 pass/skip, 1 fail.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifact_parsers as ap  # noqa: E402


def main():
    parser = argparse.ArgumentParser(
        description="Proposals must match the responsibility map's NEW/EXTEND rows")
    parser.add_argument("--feature", required=True, help="Feature root")
    args = parser.parse_args()

    feature_root = os.path.abspath(args.feature)
    resp_map = os.path.join(feature_root, "stages", "01a_responsibility-map",
                            "output", "responsibility-map.md")
    concept_out = os.path.join(feature_root, "stages", "02_concepts", "output")

    if not os.path.isfile(resp_map):
        print("SKIP  no responsibility map (Stage 01a not reached)")
        return 0

    entries = {c: e for c, e in ap.parse_responsibility_map(resp_map).items()
               if c != "Web"}
    origins = {c: (e.origin or "").strip().lower() for c, e in entries.items()}

    if not any(origins.values()):
        print("SKIP  responsibility map has no Origin column (pre-Model-B)")
        return 0

    failures = []

    # Origin vocabulary
    for concept, origin in sorted(origins.items()):
        if not (origin.startswith("new") or origin.startswith("reused")
                or origin.startswith("extend")):
            failures.append(
                f"{concept}: unrecognised Origin '{entries[concept].origin}' "
                f"(expected new / reused:UC-XX / extends:UC-XX)")

    expected = {c for c, o in origins.items()
                if o.startswith("new") or o.startswith("extend")}
    reuse = {c for c, o in origins.items() if o.startswith("reused")}
    present = set(ap.concept_spec_paths([concept_out]))

    for concept in sorted(expected - present):
        failures.append(
            f"{concept}: Origin '{entries[concept].origin}' requires a proposal "
            f"{concept}.concept.md in Stage 02 output — none found")
    for concept in sorted(present - expected):
        if concept in reuse:
            failures.append(
                f"{concept}: Origin '{entries[concept].origin}' must NOT carry a "
                f"spec file (reused concepts bind to the canonical corpus)")
        elif concept in entries:
            failures.append(
                f"{concept}: a proposal exists but the responsibility map Origin "
                f"is '{entries[concept].origin}'")
        else:
            failures.append(
                f"{concept}: a proposal exists for a concept that is not in the "
                f"responsibility map")

    if failures:
        print(f"FAIL  {len(failures)} concept-proposal mismatch(es):")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"PASS  proposals match the responsibility map "
          f"({len(expected)} new/extend, {len(reuse)} reused)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
