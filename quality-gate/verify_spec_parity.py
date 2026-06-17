#!/usr/bin/env python3
"""
verify_spec_parity.py — Stage gate: concept spec actions match SPEC entries.

Why this exists:
  The implementation compiles against SPECs, not concept specs. If an action
  is added to a concept spec but never makes it into the SPEC, the concept
  will never be exercised at runtime. This script checks that every action
  name in every concept spec has a matching entry in the corresponding SPEC
  file, and vice versa, with no extras on either side.

Checks:
  1. Every action name in *.concept.md appears in the corresponding *.spec.md
  2. Every action name in *.spec.md appears in the corresponding *.concept.md
  3. No bootstrap SPEC files without an explicit methodology deviation

Usage:
  python3 verify_spec_parity.py --concept-dir <concept-output/> --spec-dir <spec-output/>
"""

import argparse
import os
import re
import sys


def parse_concept_actions(path):
    """
    Parse a concept spec file. Return set of action names.
    Actions are identified as top-level definitions: `actionName [ args ]`
    """
    actions = set()
    concept = os.path.basename(path).replace(".concept.md", "")
    with open(path) as f:
        for line in f:
            m_action = re.match(r"^([a-z]\w+)\s+\[", line.strip())
            if m_action:
                actions.add(m_action.group(1))
    return concept, actions


def parse_spec_actions_and_outcomes(path):
    """
    Parse a SPEC file. Return dict:
      { action_name: set_of_outcome_strings }
    Outcomes are extracted from `**Outcomes` lines.
    """
    result = {}
    concept = os.path.basename(path).replace(".spec.md", "")
    with open(path) as f:
        content = f.read()

    lines = content.split("\n")
    current_action = None

    for line in lines:
        # Detect action section: ### `actionName(...)`
        m_action = re.match(r"^###\s+`(\w+)\(", line.strip())
        if m_action:
            current_action = m_action.group(1)
            result.setdefault(current_action, set())
            continue

        if current_action is None:
            continue

        # Match: - **Outcomes (enum):** `OK`, `BAD_PASSWORD`, `LOCKED`
        # Match: - **Outcomes:** `STORED` (always)
        m_out = re.match(r"^- \*\*Outcomes.*?:\*\*\s+(.+)$", line.strip())
        if m_out:
            outcomes_str = m_out.group(1)
            outcomes = re.findall(r"`([^`]+)`", outcomes_str)
            result[current_action] = set(outcomes)
            current_action = None  # Reset until next action section

    return concept, result


def normalize(name):
    """Normalize for comparison: PascalCase → SCREAMING_SNAKE_CASE, uppercase."""
    s = re.sub(r'([a-z])([A-Z])', r'\1_\2', name)
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s)
    return s.upper()


def main():
    parser = argparse.ArgumentParser(
        description="Verify concept spec actions/outcomes match SPECs")
    parser.add_argument("--concept-dir", required=True,
                        help="Path to 02_concepts/output/")
    parser.add_argument("--spec-dir", required=True,
                        help="Path to 04b_spec/output/")
    args = parser.parse_args()

    concept_dir = args.concept_dir
    spec_dir = args.spec_dir

    if not os.path.isdir(concept_dir):
        print(f"FAIL  concept directory not found: {concept_dir}")
        sys.exit(1)
    if not os.path.isdir(spec_dir):
        print(f"FAIL  spec directory not found: {spec_dir}")
        sys.exit(1)

    # Bootstrap exclusion: check no Web.spec.md exists without waiver
    web_spec = os.path.join(spec_dir, "Web.spec.md")
    if os.path.isfile(web_spec):
        print("FAIL  Web.spec.md found — bootstrap concepts must not have SPEC "
              "files without an explicit methodology deviation")
        sys.exit(1)

    concept_files = sorted([
        f for f in os.listdir(concept_dir) if f.endswith(".concept.md")
    ])
    spec_files = sorted([
        f for f in os.listdir(spec_dir) if f.endswith(".spec.md")
    ])

    # Match concept specs to SPECs by name
    concept_actions = {}
    for fname in concept_files:
        path = os.path.join(concept_dir, fname)
        concept, actions = parse_concept_actions(path)
        concept_actions[concept] = actions

    spec_actions = {}
    for fname in spec_files:
        path = os.path.join(spec_dir, fname)
        concept, actions = parse_spec_actions_and_outcomes(path)
        spec_actions[concept] = set(actions.keys())

    passed = True
    total_actions_checked = 0

    # Check: Every concept spec has a corresponding SPEC file
    for concept in sorted(concept_actions):
        if concept not in spec_actions:
            print(f"FAIL  {concept}: concept spec exists but no {concept}.spec.md")
            passed = False
            continue

        c_actions = concept_actions[concept]
        s_actions = spec_actions[concept]

        # Every action in concept spec must appear in SPEC
        missing_in_spec = c_actions - s_actions
        for action in sorted(missing_in_spec):
            print(f"FAIL  {concept}.{action}: in concept spec but not in SPEC")
            passed = False

        # Every action in SPEC must appear in concept spec
        extra_in_spec = s_actions - c_actions
        for action in sorted(extra_in_spec):
            print(f"FAIL  {concept}.{action}: in SPEC but not in concept spec")
            passed = False

        total_actions_checked += len(c_actions | s_actions)
        print(f"INFO  {concept}: {len(s_actions)} SPEC actions "
              f"↔ {len(c_actions)} concept actions")

    if passed:
        print(f"PASS  {total_actions_checked} actions match between concept "
              f"specs and SPECs across {len(spec_actions)} concepts")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
