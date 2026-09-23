#!/usr/bin/env python3
"""
verify_outcome_alignment.py — Stage gate: chain-table outcomes match contract enums.

Why this exists:
  The most common form of CLAD contract drift is an outcome name changing between
  the chain table (e.g. "Found") and the contract (e.g. "FOUND"). An LLM can miss
  this because both look similar to a human reader. This script normalises both
  sides (PascalCase → SCREAMING_SNAKE_CASE) and compares character-by-character.

Checks:
  For each chain-table row, the Outcome value (base name, stripped of payload)
  must appear in the corresponding contract's outcome enum for that action.

Usage:
  python3 verify_outcome_alignment.py \
    --chain-dir <chain-output/> \
    --contract-dir <spec-output/>
"""

import argparse
import os
import re
import sys

from artifact_parsers import (contract_actions, parse_chain_table,
                              parse_spec_outcomes, parse_spec_outcomes_multi)


def parse_chain_outcomes(chain_dir):
    """
    Parse all chain-table files. Return list of (concept, action, outcome_base).
    outcome_base is the outcome string with parenthesised payload removed.

    Terminal respond rows (whose Then carries a bracket suffix like
    `Web.respond[200]`) are skipped — they are `then` sinks, not sync
    triggers, matching the historical verify_outcome_alignment.py behaviour.
    """
    rows = []
    if not os.path.isdir(chain_dir):
        return rows
    for fname in sorted(os.listdir(chain_dir)):
        if not fname.endswith("-chain.md") or fname.endswith("-all-scenarios-chain.md"):
            continue
        for r in parse_chain_table(os.path.join(chain_dir, fname)):
            if r.then_suffix is not None:
                continue
            for outcome_base in r.outcome_bases:
                rows.append((r.then_concept, r.then_action, outcome_base))
    return rows


def _chain_row_files(chain_dir):
    """The chain files the check would read, whether or not they yield rows."""
    if not os.path.isdir(chain_dir):
        return []
    return [f for f in sorted(os.listdir(chain_dir))
            if f.endswith("-chain.md") and not f.endswith("-all-scenarios-chain.md")]


def normalize(name):
    """Normalize outcome names for comparison.
    Converts PascalCase to SCREAMING_SNAKE_CASE, then uppercases.
    Examples: "NotFound" -> "NOT_FOUND", "Ok" -> "OK", "BadPassword" -> "BAD_PASSWORD"
    """
    s = name.strip()
    # Insert underscore before uppercase letters that follow lowercase
    s = re.sub(r'([a-z])([A-Z])', r'\1_\2', s)
    # Insert underscore between consecutive uppercase and an uppercase+lowercase
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s)
    return s.upper()


def main():
    parser = argparse.ArgumentParser(
        description="Verify chain-table outcomes align with contract outcome enums")
    parser.add_argument("--chain-dir", required=True,
                        help="Path to 01b_chain-table/output/")
    parser.add_argument("--contract-dir", required=True, action="append",
                        help="Contract dir; repeatable. Earlier dirs shadow later "
                             "ones by concept name, so a reused concept is validated "
                             "against its canonical contract (R22).")
    args = parser.parse_args()

    chain_rows = parse_chain_outcomes(args.chain_dir)
    spec_outcomes = parse_spec_outcomes_multi(args.contract_dir)

    if not chain_rows:
        # Distinguish absence from defect: no chain dir (or no chain files) is a
        # legitimate skip when this stage's inputs are not present yet, but a
        # populated chain dir that parses to zero comparable rows means every
        # row was a terminal respond row — a chain table with no sync triggers.
        if not _chain_row_files(args.chain_dir):
            print(f"SKIP  no chain-table files found under {args.chain_dir}")
            sys.exit(0)
        print("FAIL  chain-table file(s) present but no comparable rows parsed — "
              "every row was a terminal respond row, so no sync-trigger outcome "
              "could be aligned. Fix the chain table (or --chain-dir).")
        sys.exit(1)

    if not spec_outcomes:
        print("FAIL  no contract outcomes parsed — check --contract-dir")
        sys.exit(1)

    passed = True
    checked = 0

    for concept, action, outcome_base in chain_rows:
        # Skip Web actions — Web is bootstrap
        if concept.lower() == "web":
            continue

        key = (concept, action)
        if key not in spec_outcomes:
            print(f"FAIL  {concept}.{action}: action not found in contracts "
                  f"(known: {sorted(spec_outcomes.keys())})")
            passed = False
            continue

        expected = spec_outcomes[key]
        outcome_norm = normalize(outcome_base)

        if outcome_norm not in {normalize(e) for e in expected}:
            print(f"FAIL  {concept}.{action}: outcome '{outcome_base}' "
                  f"(normalized: '{outcome_norm}') not in contract outcomes "
                  f"{sorted(expected)}")
            passed = False
        else:
            checked += 1

    if passed:
        print(f"PASS  {checked} chain-table outcomes aligned with contract enums")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
