#!/usr/bin/env python3
"""
verify_gate_progression.py — Stage gate: ensure human gates are not skipped.

Why this exists:
  In CLAD's 3-gate model, Stages 01–02b auto-advance to Gate 1 (02b),
  Stages 02–03b auto-advance to Gate 2 (03b), and Stages 04a–04c
  auto-advance to Gate 3 (04c). An agent can barrel through all three
  gates in one turn without stopping for human review. This script runs
  as a pre-flight at the start of every stage and checks that the
  previous gate (if any) was approved before auto-advancing further.

Gate stages:
  - Gate 1: 02b_chain-table  (human approves requirements)
  - Gate 2: 03b_data-model   (human approves architecture)
  - Gate 3: 04c_flow-tests   (human approves executable spec)

Checks:
  1. Determines the current stage from --current-stage
  2. Matches it to the nearest preceding gate stage
  3. Reads the feature's RESUME.md for gate approval evidence
  4. If the nearest preceding gate is not approved and the current
     stage is past that gate, the script fails.

Usage:
  python3 verify_gate_progression.py \
    --current-stage <stage-folder-name> \
    --resume-feature <features/UC-XX-name/RESUME.md>
"""

import argparse
import os
import re
import sys


# Gate definitions: stage folder name -> gate info
GATES = {
    "02b_chain-table": {
        "number": 1,
        "name": "Requirements",
        "next_stages_until_next_gate": {"02_concepts", "03_syncs", "03a_dependency-review"},
    },
    "03b_data-model": {
        "number": 2,
        "name": "Architecture",
        "next_stages_until_next_gate": {"04_implement", "04a_storage-mapping", "04b_spec"},
    },
    "04c_flow-tests": {
        "number": 3,
        "name": "Executable spec",
        "next_stages_until_next_gate": {"04d_concept-tdd", "04d_red-tests", "04d_green-impl",
                                          "04e_sync-tdd", "04e_red-tests", "04e_green-impl",
                                          "05_verify"},
    },
}

# Map any stage folder to its nearest preceding gate
def find_preceding_gate(stage_name):
    """Return the gate info dict for the most recent gate, or None if before Gate 1."""
    gate_order = ["02b_chain-table", "03b_data-model", "04c_flow-tests"]
    if stage_name in gate_order:
        # Current stage IS a gate — no preceding gate to check
        return None
    for i, gate in enumerate(gate_order):
        if stage_name in GATES[gate]["next_stages_until_next_gate"]:
            # Check the previous gate
            if i > 0:
                return gate_order[i - 1], GATES[gate_order[i - 1]]
            return None
    # Unknown stage — could be 01_usecase, 02a, etc. before Gate 1
    return None


def check_gate_approved(resume_path, gate_stage, gate_info):
    """Check if a gate was approved by reading RESUME.md."""
    if not os.path.isfile(resume_path):
        print(f"FAIL  RESUME.md not found: {resume_path}")
        return False

    with open(resume_path) as f:
        content = f.read()

    gate_num = gate_info["number"]
    gate_name = gate_info["name"]

    # Check for explicit approval evidence
    # Pattern 1: "Gate outcome: passed" or "Gate outcome: approved"
    # Pattern 2: "Last completed stage: {gate_stage}"
    gate_approved = False
    lines = content.split("\n")

    # Check the Gate snapshot section
    in_snapshot = False
    for line in lines:
        if "## Gate snapshot" in line:
            in_snapshot = True
            continue
        if in_snapshot:
            if line.startswith("## "):
                break
            if "Gate outcome:" in line:
                outcome = line.split(":", 1)[1].strip().lower()
                if outcome in ("passed", "approved"):
                    gate_approved = True

    return gate_approved


def main():
    parser = argparse.ArgumentParser(
        description="Verify human gates are not skipped during auto-advance")
    parser.add_argument("--current-stage", required=True,
                        help="Current stage folder name (e.g. 03_syncs, 04a_storage-mapping)")
    parser.add_argument("--resume-feature", required=True,
                        help="Path to features/UC-XX/RESUME.md")
    args = parser.parse_args()

    current = args.current_stage
    resume_path = args.resume_feature

    if not os.path.isfile(resume_path):
        print(f"FAIL  RESUME.md not found: {resume_path}")
        sys.exit(1)

    # Determine which gate this stage belongs to
    gate_order = ["02b_chain-table", "03b_data-model", "04c_flow-tests"]

    # If current stage IS a gate, no pre-gate check needed
    if current in gate_order:
        print(f"PASS  current stage '{current}' is a gate stage — no preceding gate to check")
        sys.exit(0)

    # Find which gate block this stage is in
    current_block = None
    for i, gate in enumerate(gate_order):
        gate_info = GATES[gate]
        if current in gate_info["next_stages_until_next_gate"]:
            current_block = i
            break
        if current == gate:
            current_block = i
            break

    if current_block is None:
        # Before Gate 1 (01_usecase, 02a, etc.) — no check needed
        print(f"PASS  stage '{current}' is before Gate 1 — no preceding gate to check")
        sys.exit(0)

    # Check that the gate for this block has been approved
    gate_to_check = gate_order[current_block]
    gate_info = GATES[gate_to_check]
    gate_num = gate_info["number"]
    gate_name = gate_info["name"]

    # But we need to check the PREVIOUS gate, not this block's gate
    if current_block > 0:
        prev_gate = gate_order[current_block - 1]
        prev_gate_info = GATES[prev_gate]
        prev_num = prev_gate_info["number"]
        prev_name = prev_gate_info["name"]

        if not check_gate_approved(resume_path, prev_gate, prev_gate_info):
            print(f"FAIL  Gate {prev_num} ({prev_name}) must be approved before "
                  f"advancing to stage '{current}'. "
                  f"Found no 'Gate outcome: passed' in {resume_path}. "
                  f"Present Gate {prev_num} artefacts for human review first.")
            sys.exit(1)

        print(f"PASS  Gate {prev_num} ({prev_name}) was approved — proceeding to stage '{current}'")
        sys.exit(0)
    else:
        # In Gate 1 block but before Gate 1 stage (01, 02a before 02b)
        print(f"PASS  stage '{current}' is before Gate 1 — no preceding gate to check")
        sys.exit(0)


if __name__ == "__main__":
    main()
