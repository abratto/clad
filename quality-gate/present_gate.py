#!/usr/bin/env python3
"""
present_gate.py — Output a formatted summary of artefacts for a human gate review.

Usage:
  python3 present_gate.py --feature features/UC-XX-<slug> --gate 1

Exits 0 and prints the artefact summary to stdout.
The agent MUST present this output to the human and wait for approval.
Do NOT mark the gate as approved until the human explicitly says so.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clad_stages as cs  # noqa: E402

GATE_DESCRIPTIONS = {
    1: "Use case, responsibility map, chain tables",
    2: "Concept specs, syncs, dependency review, data model",
    3: "Storage mapping, SPEC, flow tests (.feature)",
}


def main():
    parser = argparse.ArgumentParser(description="Present gate artefacts for human review")
    parser.add_argument("--feature", required=True, help="Feature root path (e.g. features/UC-XX-<slug>)")
    parser.add_argument("--gate", required=True, type=int, choices=[1, 2, 3], help="Gate number to present")
    args = parser.parse_args()

    feature_root = os.path.abspath(args.feature)
    feature_name = os.path.basename(feature_root)
    label = cs.GATE_LABELS[args.gate]
    stage_ids = cs.gate_stages(args.gate)

    print(f"=" * 60)
    print(f"  GATE {args.gate} — {label}")
    print(f"  Feature: {feature_name}")
    print(f"  {GATE_DESCRIPTIONS.get(args.gate, '')}")
    print(f"=" * 60)
    print()

    all_ok = True
    for stage_id in stage_ids:
        stage = cs.stage_by_id(stage_id)
        stage_name = stage.label if stage else stage_id
        out_dir = stage.output_dir(feature_root) if stage else ""

        if out_dir and os.path.isdir(out_dir):
            files = [f for f in os.listdir(out_dir)
                     if f != ".gitkeep" and f != ".gitkeep.md"
                     and not f.startswith(".")]
            if files:
                print(f"  {stage_name}:")
                for f in sorted(files):
                    print(f"    - {f}")
            else:
                print(f"  {stage_name}: (empty)")
                all_ok = False
        else:
            print(f"  {stage_name}: (directory not found)")
            all_ok = False

    print()
    if all_ok:
        print(f"  All stages for Gate {args.gate} have artefacts.")
    else:
        print(f"  WARNING: Some stages are missing artefacts.")
    print()
    print(f"  Present this summary to the human reviewer.")
    print(f"  Do NOT proceed until the human says 'approved'.")
    print(f"=" * 60)

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
