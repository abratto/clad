#!/usr/bin/env python3
"""
verify_outcome_alignment.py — Stage gate: chain-table outcomes match SPEC enums.

Why this exists:
  The most common form of CLAD contract drift is an outcome name changing between
  the chain table (e.g. "Found") and the SPEC (e.g. "FOUND"). An LLM can miss
  this because both look similar to a human reader. This script normalises both
  sides (PascalCase → SCREAMING_SNAKE_CASE) and compares character-by-character.

Checks:
  For each chain-table row, the Outcome value (base name, stripped of payload)
  must appear in the corresponding SPEC's outcome enum for that action.

Usage:
  python3 verify_outcome_alignment.py \
    --chain-dir <chain-output/> \
    --spec-dir <spec-output/>
"""

import argparse
import os
import re
import sys

from artifact_parsers import parse_chain_table, parse_spec_outcomes


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
            rows.append((r.then_concept, r.then_action, r.outcome_base))
    return rows


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
        description="Verify chain-table outcomes align with SPEC outcome enums")
    parser.add_argument("--chain-dir", required=True,
                        help="Path to 01b_chain-table/output/")
    parser.add_argument("--spec-dir", required=True,
                        help="Path to 04b_spec/output/")
    args = parser.parse_args()

    chain_rows = parse_chain_outcomes(args.chain_dir)
    spec_outcomes = parse_spec_outcomes(args.spec_dir)

    if not chain_rows:
        print("WARN  no chain rows found — check --chain-dir")
        sys.exit(0)

    if not spec_outcomes:
        print("FAIL  no SPEC outcomes parsed — check --spec-dir")
        sys.exit(1)

    passed = True
    checked = 0

    for concept, action, outcome_base in chain_rows:
        # Skip Web actions — Web is bootstrap
        if concept.lower() == "web":
            continue

        key = (concept, action)
        if key not in spec_outcomes:
            print(f"FAIL  {concept}.{action}: action not found in SPECs "
                  f"(known: {sorted(spec_outcomes.keys())})")
            passed = False
            continue

        expected = spec_outcomes[key]
        outcome_norm = normalize(outcome_base)

        if outcome_norm not in {normalize(e) for e in expected}:
            print(f"FAIL  {concept}.{action}: outcome '{outcome_base}' "
                  f"(normalized: '{outcome_norm}') not in SPEC outcomes "
                  f"{sorted(expected)}")
            passed = False
        else:
            checked += 1

    if passed:
        print(f"PASS  {checked} chain-table outcomes aligned with SPEC enums")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
