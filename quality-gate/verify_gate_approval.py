#!/usr/bin/env python3
"""
verify_gate_approval.py — Deterministic gate-approval check.

Why this exists:
  Previously, stage pre-conditions were human-readable prose ("Check RESUME.md
  for Gate 1: Approved") that an LLM could silently skip reading. This script
  makes the check deterministic: it reads the feature's RESUME.md, confirms
  the required gates are marked `approved` (human) or `auto-approved`
  (workflow.autonomous=true), and cross-validates that the corresponding stage
  output directories are non-empty. Human approvals are additionally bound to
  a content hash; auto-approved gates are exempt. It exits non-zero if any
  check fails, stopping the pipeline before the next stage starts.

Usage:
  python3 verify_gate_approval.py \\
    --feature features/UC-XX-<slug> \\
    --required-gates 1[,2,3]

Gate to stage output mapping (for cross-validation):
  Gate 1 -> stages/01b_chain-table/output/
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clad_stages as cs  # noqa: E402
from verify_stage_sequence import (  # noqa: E402
    APPROVED_STATES,
    compute_gate_hash,
    gate_hash_recorded,
)


GATE_LABELS = cs.GATE_LABELS


def gate_output_dir(feature_root: str, gate_num: int) -> Optional[str]:
    """The output directory of the gate's marker stage (the last stage the
    gate approves), derived from the shared stage model — not a local copy."""
    block = cs.gate_stages(gate_num)
    stage = cs.stage_by_id(block[-1]) if block else None
    return stage.output_dir(feature_root) if stage else None


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
        pattern = rf"^- \*\*Gate {gate_num} \({re.escape(label)}\):\*\*\s+`([\w-]+)`"
        match = re.search(pattern, content, re.MULTILINE)
        if not match:
            print(f"FAIL  Gate {gate_num} ({label}) line not found in {resume_path}")
            print(f"       Expected pattern: - **Gate {gate_num} ({label}):** `<status>`")
            all_passed = False
            continue
        status = match.group(1)
        if status not in APPROVED_STATES:
            print(f"FAIL  Gate {gate_num} ({label}) is not approved in "
                  f"{resume_path} (found '{status}')")
            all_passed = False
            continue
        # Cross-check: output directory exists and is non-empty
        out_dir = gate_output_dir(feature_root, gate_num)
        if out_dir:
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
        # auto-approved gates are the documented "a human never reviewed this"
        # escape hatch (workflow.autonomous=true). They carry no content hash
        # and are exempt from staleness, matching verify_stage_sequence.
        if status == "auto-approved":
            print(f"PASS  Gate {gate_num} ({label}) — auto-approved, output present")
            continue
        # Content binding: a human approval is bound to the hash of the gate's
        # stages. Missing hash = legacy approval (must be re-baselined); a
        # mismatch = the artefacts changed since approval (must be re-presented).
        recorded = gate_hash_recorded(content, gate_num)
        if recorded is None:
            print(f"FAIL  Gate {gate_num} ({label}) has no content hash — "
                  f"approved by an older workflow. Re-approve with "
                  f"approve_gate.py --gate {gate_num} (or --baseline).")
            all_passed = False
            continue
        current = compute_gate_hash(feature_root, gate_num)
        if recorded != current:
            print(f"FAIL  Gate {gate_num} ({label}) approval is stale — the "
                  f"artefacts changed since approval. Re-present the gate.")
            all_passed = False
            continue
        print(f"PASS  Gate {gate_num} ({label}) — approved, output present, "
              f"content hash matches")

    if all_passed:
        print(f"PASS  all {len(required_gates)} required gates approved")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
