#!/usr/bin/env python3
"""
verify_chain_map_names.py — Stage 01b gate: every chain-table action name
resolves against the Stage 01a responsibility map.

Why this exists:
  The chain table is the CANONICAL name source downstream ("if a Stage 03
  sync spec disagrees with a chain table on an action name, the chain table
  wins"). That rule only works when the chain table's names were themselves
  agreed at 01a — a chain row naming an action the responsibility map never
  declared means the name was invented mid-choreography, and the
  "chain table wins" adjudication then propagates an unreviewed name into
  concept specs, syncs, and contracts (maintenance change
  `staged-naming-discipline`).

This is the name-level, design-time slice of verify_action_chain.py: the
full check runs at 04b (when sync specs, cards, and contracts exist); this
one runs at Gate 1 with only the two artefacts that exist by then.

Web actions are exempt (the bootstrap concept's request/respond surface is
owned by the transport profile, not the responsibility map's vocabulary
discussion).

Usage:
  python3 verify_chain_map_names.py --resp-map <responsibility-map.md> \
                                    --chain-dir <01b_chain-table/output/>

Exit: 0 pass/skip, 1 fail.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifact_parsers as ap  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chain-table action names must resolve against the 01a map")
    parser.add_argument("--resp-map", required=True,
                        help="Path to 01a responsibility-map.md")
    parser.add_argument("--chain-dir", required=True,
                        help="Path to 01b_chain-table/output/")
    args = parser.parse_args()

    if not os.path.isfile(args.resp_map):
        print("SKIP  no responsibility map (Stage 01a not reached)")
        return 0
    if not os.path.isdir(args.chain_dir):
        print("SKIP  no chain-table output (Stage 01b not reached)")
        return 0

    declared = ap.parse_resp_map_actions(args.resp_map)
    chained = ap.parse_chain_table_actions(args.chain_dir)

    # Web is the bootstrap concept: exempt from the vocabulary check.
    declared = {a for a in declared if not a.startswith("Web/")}
    chained = {a for a in chained if not a.startswith("Web/")}

    if not chained:
        print("SKIP  no actions parsed from the chain tables")
        return 0

    undeclared = sorted(chained - declared)
    if undeclared:
        print(f"FAIL  {len(undeclared)} chained action(s) not declared in the "
              f"responsibility map:")
        for action in undeclared:
            concept, _, name = action.partition("/")
            print(f"  - {action} — add `{name}` to {concept}'s Owned actions "
                  f"in the 01a map, or fix the chain-table name")
        return 1

    print(f"PASS  {len(chained)} chained action(s) resolve against the "
          f"responsibility map ({len(declared)} declared)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
