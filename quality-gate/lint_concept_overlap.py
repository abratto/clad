#!/usr/bin/env python3
"""
lint_concept_overlap.py — advisory linter: NEW proposals that overlap an
existing catalog concept are surfaced as warnings, never failures.

Why this exists:
  verify_concept_novelty.py blocks only when a near-match is UNJUSTIFIED.
  This linter additionally surfaces the justified ones (and runs even when
  the novelty gate skips), so a reviewer at Gate 1 sees every close call in
  one place. Novelty is legitimate — the warning exists so the decision is
  made with the overlap visible, not discovered at Stage 04
  (maintenance change `concept-novelty-gate`).

Always exits 0.

Usage:
  python3 lint_concept_overlap.py --feature features/UC-XX-<slug>
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifact_parsers as ap  # noqa: E402
import clad_stages as cs  # noqa: E402
import concept_novelty as cn  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Advisory: warn on NEW concepts overlapping the catalog")
    parser.add_argument("--feature", required=True, help="Feature root")
    args = parser.parse_args()

    feature_root = os.path.abspath(args.feature)
    resp_map = os.path.join(feature_root, "stages", "01a_responsibility-map",
                            "output", "responsibility-map.md")
    if not os.path.isfile(resp_map):
        print("SKIP  no responsibility map (Stage 01a not reached)")
        return 0

    entries = {c: e for c, e in ap.parse_responsibility_map(resp_map).items()
               if c != "Web"}
    new_concepts = {c: e for c, e in entries.items()
                    if (e.origin or "").strip().lower().startswith("new")}
    if not new_concepts:
        print("SKIP  no NEW concept rows")
        return 0

    catalog_path = os.path.join(
        os.path.dirname(feature_root), "_system", "concepts-catalog.md")
    catalog = cn.load_catalog_tokens(catalog_path)
    if not catalog:
        print("SKIP  no concepts catalog (first feature)")
        return 0

    configured = cs.get_property(feature_root, "concept.novelty.threshold")
    threshold = (cn.parse_threshold(configured) if configured
                 else cn.DEFAULT_THRESHOLD)

    warnings = 0
    for concept in sorted(new_concepts):
        tokens = cn.proposal_tokens(concept,
                                    new_concepts[concept].owned_actions)
        for name, score in cn.near_matches(tokens, catalog, threshold):
            warnings += 1
            shared = sorted(tokens & catalog[name])
            print(f"WARN  {concept} overlaps {name} ({score:.2f}) — shared "
                  f"tokens: {', '.join(shared)}. Justify in `## Why not "
                  f"existing` or reconsider the Origin.")

    if not warnings:
        print(f"PASS  {len(new_concepts)} NEW concept(s) show no overlap "
              f"above threshold {threshold}")
    else:
        print(f"LINT  {warnings} overlap warning(s) above threshold "
              f"{threshold} (advisory — exit 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
