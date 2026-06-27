#!/usr/bin/env python3
"""
verify_gate_approval.py — Deterministic gate-approval check.

Why this exists:
  Previously, stage pre-conditions were human-readable prose ("Check RESUME.md
  for Gate 1: Approved") that an LLM could silently skip reading. This script
  makes the check deterministic: it reads the feature's RESUME.md, confirms
  the required gates are marked "approved", and cross-validates that the
  corresponding stage output directories are non-empty. It exits non-zero if
  any check fails, stopping the pipeline before the next stage starts.

Usage:
  python3 verify_gate_approval.py \\
    --feature features/UC-XX-<slug> \\
    --required-gates 1[,2,3]

Gate to stage output mapping (for cross-validation):
  Gate 1 -> stages/02b_chain-table/output/
  Gate 2 -> stages/03b_data-model/output/
  Gate 3 -> stages/04_implement/04c_flow-tests/output/

Exit codes:
  0  — all gates approved and output directories non-empty
  1  — one or more checks failed
"""

import argparse
import os
import re
import sys


GATE_LABELS = {
    1: "Requirements",
    2: "Architecture",
    3: "Executable spec",
}

GATE_OUTPUT_DIRS = {
    1: os.path.join("stages", "02b_chain-table", "output"),
    2: os.path.join("stages", "03b_data-model", "output"),
    3: os.path.join("stages", "04_implement", "04c_flow-tests", "output"),
}


def main():
    parser = argparse.ArgumentParser(
        description="Verify human gate approvals in a feature's RESUME.md")
    parser.add_argument("--feature", required=True,
                        help="Path to the feature root (e.g. features/UC-XX-<slug>)")
    parser.add_argument("--required-gates", required=True,
                        help="Comma-separated list of gate numbers (e.g. '1' or '1,2,3')")
    args = parser.parse_args()

    feature_root = os.path.abspath(args.feature)
    required_gates = [int(g.strip()) for g in args.required_gates.split(",")]

    resume_path = os.path.join(feature_root, "RESUME.md")
    if not os.path.isfile(resume_path):
        print(f"FAIL  RESUME.md not found at {resume_path}")
        sys.exit(1)

    with open(resume_path, "r") as f:
        content = f.read()

    # Check for ## Gate snapshot section
    if "## Gate snapshot" not in content:
        print(f"FAIL  RESUME.md is missing '## Gate snapshot' section ({resume_path})")
        sys.exit(1)

    all_passed = True

    for gate_num in required_gates:
        label = GATE_LABELS.get(gate_num, f"Gate {gate_num}")
        pattern = rf"^- \*\*Gate {gate_num} \({re.escape(label)}\):\*\*\s+`(\w+)`"
        match = re.search(pattern, content, re.MULTILINE)
        if not match:
            print(f"FAIL  Gate {gate_num} ({label}) line not found in {resume_path}")
            print(f"       Expected pattern: - **Gate {gate_num} ({label}):** `<status>`")
            all_passed = False
            continue
        status = match.group(1)
        if status != "approved":
            print(f"FAIL  Gate {gate_num} ({label}) is not 'approved' in {resume_path} "
                  f"(found '{status}')")
            all_passed = False
            continue
        # Cross-check: output directory exists and is non-empty
        rel_dir = GATE_OUTPUT_DIRS.get(gate_num)
        if rel_dir:
            out_dir = os.path.join(feature_root, rel_dir)
            if not os.path.isdir(out_dir):
                print(f"FAIL  Gate {gate_num} output directory not found: {out_dir}")
                all_passed = False
                continue
            files = [f for f in os.listdir(out_dir)
                     if f != ".gitkeep" and f != ".gitkeep.md"]
            if not files:
                print(f"FAIL  Gate {gate_num} output directory is empty: {out_dir}")
                all_passed = False
                continue
        print(f"PASS  Gate {gate_num} ({label}) — approved, output present")

    if all_passed:
        print(f"PASS  all {len(required_gates)} required gates approved")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
