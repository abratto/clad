#!/usr/bin/env python3
"""
verify_action_chain.py — Stage gate: action names flow consistently through
the full artefact chain: responsibility map → chain table → concept spec →
sync spec → dependency card → SPEC.

Why this exists:
  An action name can change in one artefact (e.g. a refactor in the chain table)
  without being updated downstream (concept spec, sync, card, SPEC). This script
  cross-references every Concept/action pair across all 6 artefact types and
  reports any that appear in one but not another. The chain tables are the
  reference — every action they invoke must appear everywhere downstream.

  The internal representation uses "/" as the separator (matching the paper's
  URI hierarchy scheme). Sync files use paper syntax (Concept/action:). Chain
  tables use dot notation (Concept.action) and are normalized on extraction.

Usage:
  python3 verify_action_chain.py \
    --resp-map <resp-map.md> \
    --chain-dir <chain-output/> \
    --concept-dir <concept-output/> \
    --sync-dir <sync-output/> \
    --dep-dir <dep-output/> \
    --spec-dir <spec-output/>
"""

import argparse
import sys

from artifact_parsers import (
    parse_resp_map_actions,
    parse_chain_table_actions,
    parse_concept_actions,
    parse_sync_actions,
    parse_dep_card_actions,
    parse_spec_actions,
)


def main():
    parser = argparse.ArgumentParser(
        description="Verify action names flow consistently across all artefacts")
    parser.add_argument("--resp-map", required=True,
                        help="Path to 01a responsibility-map.md")
    parser.add_argument("--chain-dir", required=True,
                        help="Path to 01b_chain-table/output/")
    parser.add_argument("--concept-dir", required=True,
                        help="Path to 02_concepts/output/")
    parser.add_argument("--sync-dir", required=True,
                        help="Path to 03_syncs/output/ (spec files)")
    parser.add_argument("--dep-dir", required=True,
                        help="Path to 03a_dependency-review/output/")
    parser.add_argument("--spec-dir", required=True,
                        help="Path to 04b_spec/output/")
    args = parser.parse_args()

    sources = {
        "responsibility map":  parse_resp_map_actions(args.resp_map),
        "chain tables":        parse_chain_table_actions(args.chain_dir),
        "concept specs":       parse_concept_actions(args.concept_dir),
        "sync specs":          parse_sync_actions(args.sync_dir),
        "dep. cards":          parse_dep_card_actions(args.dep_dir),
        "SPECs":               parse_spec_actions(args.spec_dir),
    }

    # Filter out Web actions for all sources (Web is bootstrap)
    for name in sources:
        sources[name] = {a for a in sources[name] if not a.startswith("Web/")}

    if not any(sources.values()):
        print("FAIL  no actions parsed from any source")
        sys.exit(1)

    for name, actions in sources.items():
        print(f"INFO  {name}: {len(actions)} actions — {sorted(actions)}")

    # The chain tables are the reference for what the current feature
    # actually invokes. Every chained action must appear in all other
    # artefact types. Upstream artefacts (resp map, concept specs) may
    # declare extra actions not exercised by this UC — that is legal
    # (e.g. User.register, Session.lookup exist for future use cases).
    reference = sources["chain tables"]
    if not reference:
        reference = sources.get("sync specs", set())
    if not reference:
        print("FAIL  no reference actions (chain tables or sync specs)")
        sys.exit(1)

    passed = True
    for action in sorted(reference):
        missing_in = []
        for name, actions in sources.items():
            if name == "chain tables":
                continue
            if action not in actions:
                missing_in.append(name)
        if missing_in:
            print(f"FAIL  {action} (used in chain) missing from: "
                  f"{', '.join(missing_in)}")
            passed = False

    # Also check that responsibility map declares every chained action
    chained_not_in_resp = reference - sources["responsibility map"]
    if chained_not_in_resp:
        for a in sorted(chained_not_in_resp):
            print(f"FAIL  {a} used in chain but not declared in "
                  f"responsibility map")
        passed = False

    if passed:
        n = len(reference)
        total = sum(len(s) for s in sources.values())
        print(f"PASS  {n} chained actions flow consistently across "
              f"{len(sources)} artefact types ({total} total references)")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
