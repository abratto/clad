#!/usr/bin/env python3
"""verify_reused_concept_contracts.py — a REUSED concept must have a canonical
contract in the corpus.

Why this exists:
  A feature whose responsibility map marks a concept `reused:UC-XX` does not
  derive a contract for it — it BINDS the canonical one. If the corpus has no
  `<Name>.contract.md`, the Stage 04b parity checks (`outcome_alignment`,
  `action_chain`) fail on that concept with no explanation.

  Promotion runs at Gate 2, but contracts are produced at 04b, so a concept
  introduced/extended before this defect was fixed has a canonical spec and
  data-model but no canonical contract (experiment defect D43: the first
  pure-reuse feature, UC-04, failed on `MemberEnrolment.checkEnrolled`).

  This check turns that silent surprise into a deterministic, actionable stop:
  re-run the IDEMPOTENT promotion for the feature that last derived the concept
  (its `Introduced by`/`Used by` row in `concepts-catalog.md`), which now
  publishes the contract companion.

Usage:
  python3 verify_reused_concept_contracts.py --feature features/UC-XX-<slug>

Exit: 0 pass/skip, 1 a reused concept has no canonical contract.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifact_parsers as ap  # noqa: E402
import clad_stages as cs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reused concepts must bind a canonical contract")
    parser.add_argument("--feature", required=True)
    args = parser.parse_args()

    feature_root = os.path.abspath(args.feature)
    resp = os.path.join(feature_root, "stages", "01a_responsibility-map",
                        "output", "responsibility-map.md")
    if not os.path.isfile(resp):
        print("SKIP  no responsibility map — nothing to check")
        return 0

    corpus = cs._concept_corpus_dir(feature_root)
    if not corpus:
        print("SKIP  no concept corpus — nothing to bind")
        return 0

    reused = []
    for concept, entry in sorted(ap.parse_responsibility_map(resp).items()):
        if concept == "Web":
            continue
        if (entry.origin or "").strip().lower().startswith("reused"):
            reused.append(concept)

    if not reused:
        print("PASS  no reused concepts (no canonical contract required)")
        return 0

    missing = [c for c in reused
               if not os.path.isfile(os.path.join(corpus, c + ".contract.md"))]
    if missing:
        slug = os.path.basename(feature_root.rstrip("/"))
        print("FAIL  reused concept(s) have no canonical contract to bind: "
              + ", ".join(missing))
        print("      A reused concept binds the canonical contract, but the corpus "
              "has none.")
        print("      Promotion runs at Gate 2 (before 04b derives contracts), so a "
              "concept introduced/extended earlier may lack one.")
        print("      Remedy (idempotent): re-run promotion for the feature that "
              "last derived the concept")
        print("      — see its `Introduced by`/`Used by` row in "
              "features/_system/concepts-catalog.md:")
        print(f"        ./clad promote-concepts <that-feature>")
        print(f"      (this feature is `{slug}`; if it extends the concept, "
              f"`./clad promote-concepts {slug}` also publishes it.)")
        return 1

    print(f"PASS  {len(reused)} reused concept(s) bind a canonical contract")
    return 0


if __name__ == "__main__":
    sys.exit(main())
