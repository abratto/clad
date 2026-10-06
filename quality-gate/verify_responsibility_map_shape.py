#!/usr/bin/env python3
"""
verify_responsibility_map_shape.py — Stage 01a gate: the Concepts table's
`Owned actions` column carries NAMES ONLY — no signatures, no outcomes.

Why this exists:
  Stage 01a fixes the concept SET and the action VOCABULARY; signatures and
  outcome enums are Stage 02 / 01b work. Writing them at 01a locks a
  half-agreed design into the artefact the chain tables (01b) and concept
  specs (02) are then derived from — the walkthrough's agent stance
  ("if you find yourself writing `lookupByUsername(username) -> Found(userId)`,
  you are doing Stage 02 work in Stage 01a") was a social rule; this check
  makes it mechanical (maintenance change `staged-naming-discipline`).

Rejected tokens in the raw `Owned actions` cell:
  * `(` or `)`   — a parameter list (a signature)
  * `->`         — a return-type annotation (a signature)
  * `[` or `]`   — an outcome enum (`[ ok ]`, `[ error: "…" ]`)

Bare backticked action names (and commas) are the only legal content.
The Concepts table's OTHER columns are not checked here: `Owned state` may
legitimately carry types (`Map<WidgetId, Widget>`).

Usage:
  python3 verify_responsibility_map_shape.py --resp-map <responsibility-map.md>

Exit: 0 pass/skip, 1 fail.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifact_parsers as ap  # noqa: E402

_FORBIDDEN = (
    ("(", "a parameter list — signatures are Stage 02 work"),
    (")", "a parameter list — signatures are Stage 02 work"),
    ("->", "a return-type annotation — signatures are Stage 02 work"),
    ("[", "an outcome enum — outcomes are Stage 01b/02 work"),
    ("]", "an outcome enum — outcomes are Stage 01b/02 work"),
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="01a Owned actions column must carry names only, "
                    "no signatures or outcomes")
    parser.add_argument("--resp-map", required=True,
                        help="Path to 01a responsibility-map.md")
    args = parser.parse_args()

    if not os.path.isfile(args.resp_map):
        print("SKIP  no responsibility map (Stage 01a not reached)")
        return 0

    cells = ap.parse_resp_map_action_cells(args.resp_map)
    if not cells:
        print("SKIP  no Concepts table found in the responsibility map")
        return 0

    failures = []
    for concept in sorted(cells):
        cell = cells[concept]
        for token, why in _FORBIDDEN:
            if token in cell:
                failures.append(
                    f"{concept}: Owned actions cell contains '{token}' — {why}. "
                    f"Cell: {cell.strip()}")
                break  # one diagnostic per row is enough to act on

    if failures:
        print(f"FAIL  {len(failures)} responsibility-map row(s) carry "
              f"Stage 02 detail:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"PASS  {len(cells)} concept row(s) declare action names only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
