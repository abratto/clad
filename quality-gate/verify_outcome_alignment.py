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


def parse_chain_outcomes(chain_dir):
    """
    Parse all chain-table files. Return list of (concept, action, outcome_base).
    outcome_base is the outcome string with parenthesised payload removed.
    """
    rows = []
    if not os.path.isdir(chain_dir):
        return rows

    for fname in sorted(os.listdir(chain_dir)):
        if not fname.endswith("-chain.md"):
            continue
        path = os.path.join(chain_dir, fname)
        with open(path) as f:
            content = f.read()

        # Find the markdown table. Look for separator line (|---|---|)
        lines = content.split("\n")
        in_table = False
        for line in lines:
            # Detect table separator row
            if re.match(r"^\|[-:\s]+\|[-:\s]+", line):
                in_table = True
                continue
            if not in_table:
                continue
            # Stop at first blank line or non-table line after table starts
            if line.strip() == "" or not line.startswith("|"):
                in_table = False
                continue
            # Skip header row
            if "#" in line.split("|")[1] if len(line.split("|")) > 1 else False:
                continue

            # Parse data row: # | When | Then | Inputs | Outcome | Why
            cols = [c.strip() for c in line.split("|")]
            if len(cols) < 6:
                continue
            then_col = cols[3]  # Then column
            outcome_col = cols[5]  # Outcome column

            # Extract Concept.action from Then column: `User.lookupByUsername`
            m = re.match(r"`([A-Za-z]+)\.([A-Za-z]+)`", then_col)
            if not m:
                continue
            concept = m.group(1)
            action = m.group(2)

            # Extract base outcomes from outcome column:
            # `Found(userId)` → Found, `Ok` → Ok, `Sent` → Sent
            # `AVAILABLE`, `UNAVAILABLE` → AVAILABLE, UNAVAILABLE
            outcomes = re.findall(r"`([^`]+)`", outcome_col)
            for outcome_raw in outcomes:
                outcome_base = re.sub(r"\(.*?\)", "", outcome_raw).strip()
                rows.append((concept, action, outcome_base))

    return rows


def parse_spec_outcomes(spec_dir):
    """
    Parse all SPEC files. Return dict:
      { (concept, action): set_of_outcomes }
    where outcomes are SCREAMING_SNAKE_CASE.
    """
    specs = {}
    if not os.path.isdir(spec_dir):
        return specs

    for fname in sorted(os.listdir(spec_dir)):
        if not fname.endswith(".spec.md"):
            continue
        concept = fname.replace(".spec.md", "")
        path = os.path.join(spec_dir, fname)
        with open(path) as f:
            content = f.read()

        # Find each action section: ### `actionName(...)`
        # Then find the Outcomes line under it.
        action = None
        for line in content.split("\n"):
            m_action = re.match(r"^###\s+`(\w+)\(", line)
            if m_action:
                action = m_action.group(1)
                specs.setdefault((concept, action), set())
                continue
            if action is None:
                continue
            # Match: - **Outcomes (enum):** `OK`, `BAD_PASSWORD`, `LOCKED`
            # Match: - **Outcomes:** `STORED` (always)
            m_out = re.match(r"^- \*\*Outcomes.*?:\*\*\s+(.+)$", line.strip())
            if m_out:
                outcomes_str = m_out.group(1)
                # Extract backtick-quoted values: `OK`, `BAD_PASSWORD`, `LOCKED`
                outcomes = re.findall(r"`([^`]+)`", outcomes_str)
                specs[(concept, action)] = set(outcomes)
                action = None  # Reset until next action section

    return specs


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
                        help="Path to 02b_chain-table/output/")
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
