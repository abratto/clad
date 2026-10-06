#!/usr/bin/env python3
"""
verify_concept_novelty.py — Gate-1 check: a NEW concept proposal must
justify why nothing in the canonical corpus already fits.

Why this exists:
  "Reuse is roughly 90% of design" (CONCEPTS.md) was aspirational: nothing
  forced a Stage-01a author to consult the generated catalog before writing
  `new` in the Origin column, and per-feature re-derivation of an existing
  concept is the cross-feature drift R22 exists to prevent (six divergent
  `Session.concept.md` across six use cases in the Conduit rebuild). This
  check makes the consultation auditable (maintenance change
  `concept-novelty-gate`): when a `new` proposal overlaps an existing
  catalog concept above `concept.novelty.threshold`, the responsibility map
  must carry a `## Why not existing` section explaining the non-fit per
  near-match — a checklist item, not a ban (novelty is legitimate, just
  rarely).

Skips (exit 0) when: the responsibility map is absent, the map has no
Origin column (pre-Model-B), or the catalog is absent/empty (a project's
first feature — every row is legitimately `new`).

Usage:
  python3 verify_concept_novelty.py --feature features/UC-XX-<slug>

Exit: 0 pass/skip, 1 fail.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifact_parsers as ap  # noqa: E402
import clad_stages as cs  # noqa: E402
import concept_novelty as cn  # noqa: E402

WHY_NOT_SECTION = re.compile(r"^##\s+Why not existing\b", re.MULTILINE)


def _why_not_section_text(resp_map_text: str) -> str:
    """The body of the `## Why not existing` section, or '' when absent."""
    match = WHY_NOT_SECTION.search(resp_map_text)
    if not match:
        return ""
    rest = resp_map_text[match.end():]
    nxt = re.search(r"^##\s", rest, re.MULTILINE)
    return rest[:nxt.start()] if nxt else rest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="NEW concept proposals must justify non-fit against "
                    "near-match catalog concepts")
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
    origins = {c: (e.origin or "").strip().lower() for c, e in entries.items()}
    if not any(origins.values()):
        print("SKIP  responsibility map has no Origin column (pre-Model-B)")
        return 0

    catalog_path = os.path.join(
        os.path.dirname(feature_root), "_system", "concepts-catalog.md")
    catalog = cn.load_catalog_tokens(catalog_path)
    if not catalog:
        print("SKIP  no concepts catalog (first feature — nothing to "
              "collide with)")
        return 0

    raw = cn.DEFAULT_THRESHOLD
    configured = cs.get_property(feature_root, "concept.novelty.threshold")
    threshold = cn.parse_threshold(configured) if configured else raw

    with open(resp_map, encoding="utf-8") as handle:
        resp_map_text = handle.read()
    why_not = _why_not_section_text(resp_map_text)

    failures = []
    checked = 0
    for concept in sorted(c for c, o in origins.items()
                          if o.startswith("new")):
        tokens = cn.proposal_tokens(concept, entries[concept].owned_actions)
        matches = cn.near_matches(tokens, catalog, threshold)
        if not matches:
            continue
        checked += 1
        unjustified = [name for name, _ in matches
                       if not re.search(rf"`?\b{re.escape(name)}\b`?",
                                        why_not)]
        if unjustified:
            failures.append(
                f"{concept}: overlaps existing concept(s) "
                f"{', '.join(f'{n} ({s:.2f})' for n, s in matches)} but the "
                f"responsibility map's `## Why not existing` section does not "
                f"explain the non-fit for: {', '.join(unjustified)}")

    if failures:
        print(f"FAIL  {len(failures)} unjustified NEW concept(s) "
              f"(threshold {threshold}):")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    new_count = sum(1 for o in origins.values() if o.startswith("new"))
    print(f"PASS  {new_count} NEW concept(s) checked against the catalog "
          f"({checked} with near-matches, all justified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
