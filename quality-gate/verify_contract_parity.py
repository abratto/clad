#!/usr/bin/env python3
"""
verify_contract_parity.py — Stage gate: concept spec actions match contract entries.

Why this exists:
  The implementation compiles against contracts, not concept specs. If an action
  is added to a concept spec but never makes it into the contract, the concept
  will never be exercised at runtime. This script checks that every action
  name in every concept spec has a matching entry in the corresponding contract
  file, and vice versa, with no extras on either side.

Checks:
  1. Every action name in *.concept.md appears in the corresponding *.contract.md
  2. Every action name in *.contract.md appears in the corresponding *.concept.md
  3. No bootstrap contract files without an explicit methodology deviation

Usage:
  python3 verify_contract_parity.py --concept-dir <concept-output/> --contract-dir <spec-output/>
"""

import argparse
import os
import re
import sys

from artifact_parsers import parse_concept
import artifact_parsers as ap


def parse_concept_actions(path):
    """
    Parse a concept spec file. Return (concept, set of action names).
    Actions are identified as top-level definitions: `actionName [ args ]`
    """
    concept_spec = parse_concept(path)
    return concept_spec.name, {a.name for a in concept_spec.actions}


def parse_spec_actions_and_outcomes(path):
    """
    Parse a contract file. Return (concept, { action_name: set_of_outcome_strings }).
    Outcomes are extracted from `**Outcomes` lines.
    """
    concept = os.path.basename(path).replace(".contract.md", "")
    result = {}
    with open(path) as f:
        content = f.read()

    current_action = None
    for line in content.split("\n"):
        m_action = re.match(r"^###\s+`(\w+)\(", line.strip())
        if m_action:
            current_action = m_action.group(1)
            result.setdefault(current_action, set())
            continue
        if current_action is None:
            continue
        m_out = re.match(r"^- \*\*Outcomes.*?:\*\*\s+(.+)$", line.strip())
        if m_out:
            outcomes = re.findall(r"`([^`]+)`", m_out.group(1))
            result[current_action] = set(outcomes)
            current_action = None

    return concept, result


def normalize(name):
    """Normalize for comparison: PascalCase → SCREAMING_SNAKE_CASE, uppercase."""
    s = re.sub(r'([a-z])([A-Z])', r'\1_\2', name)
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s)
    return s.upper()


def main():
    parser = argparse.ArgumentParser(
        description="Verify concept spec actions/outcomes match contracts")
    parser.add_argument("--concept-dir", required=True, action="append",
                        help="Concept-spec dir; repeatable. Earlier dirs shadow "
                             "later ones by concept name.")
    parser.add_argument("--contract-dir", required=True,
                        help="Path to 04b_contract/output/")
    args = parser.parse_args()

    concept_dirs = args.concept_dir
    contract_dir = args.contract_dir

    missing = [d for d in concept_dirs if not os.path.isdir(d)]
    if missing:
        print(f"FAIL  concept directory not found: {missing[0]}")
        sys.exit(1)
    if not os.path.isdir(contract_dir):
        print(f"FAIL  spec directory not found: {contract_dir}")
        sys.exit(1)

    # Bootstrap exclusion: check no Web.contract.md exists without waiver
    web_spec = os.path.join(contract_dir, "Web.contract.md")
    if os.path.isfile(web_spec):
        print("FAIL  Web.contract.md found — bootstrap concepts must not have contract "
              "files without an explicit methodology deviation")
        sys.exit(1)

    spec_files = sorted([
        f for f in os.listdir(contract_dir) if f.endswith(".contract.md")
    ])

    # Match concept specs to contracts by name. Concept sources are merged across
    # dirs, a feature's own proposal shadowing the canonical corpus spec.
    concept_actions = {}
    for concept, path in sorted(ap.concept_spec_paths(concept_dirs).items()):
        _, actions = parse_concept_actions(path)
        concept_actions[concept] = actions

    spec_actions = {}
    for fname in spec_files:
        path = os.path.join(contract_dir, fname)
        concept, actions = parse_spec_actions_and_outcomes(path)
        spec_actions[concept] = set(actions.keys())

    passed = True
    total_actions_checked = 0

    # Every contract must have a corresponding concept spec. The check runs
    # contract-first, not concept-first: the concept sources are the feature's
    # proposals *plus the whole canonical corpus*, so the union also holds
    # concepts this feature does not use. That every concept the feature DOES
    # use has a contract is enforced by the 04b file manifest (one contract per
    # responsibility-map concept).
    for concept in sorted(spec_actions):
        if concept not in concept_actions:
            print(f"FAIL  {concept}.contract.md exists but no concept spec was found "
                  f"for `{concept}`")
            passed = False
            continue

        c_actions = concept_actions[concept]
        s_actions = spec_actions[concept]

        # Every action in concept spec must appear in contract
        missing_in_spec = c_actions - s_actions
        for action in sorted(missing_in_spec):
            print(f"FAIL  {concept}.{action}: in concept spec but not in contract")
            passed = False

        # Every action in contract must appear in concept spec
        extra_in_spec = s_actions - c_actions
        for action in sorted(extra_in_spec):
            print(f"FAIL  {concept}.{action}: in contract but not in concept spec")
            passed = False

        total_actions_checked += len(c_actions | s_actions)
        print(f"INFO  {concept}: {len(s_actions)} contract actions "
              f"↔ {len(c_actions)} concept actions")

    if passed:
        print(f"PASS  {total_actions_checked} actions match between concept "
              f"specs and contracts across {len(spec_actions)} concepts")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
