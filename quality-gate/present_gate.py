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

# Stage IDs grouped by gate
GATE_STAGES = {
    1: {
        "label": "Requirements",
        "stages": ["01", "02a", "02b"],
        "description": "Use case, responsibility map, chain tables"
    },
    2: {
        "label": "Architecture",
        "stages": ["02", "03", "03a", "03b"],
        "description": "Concept specs, syncs, dependency review, data model"
    },
    3: {
        "label": "Executable specification",
        "stages": ["04a", "04b", "04c"],
        "description": "Storage mapping, SPEC, flow tests (.feature)"
    },
}

STAGE_NAMES = {
    "01": "Use case",
    "02a": "Responsibility map",
    "02b": "Chain table",
    "02": "Concept specs",
    "03": "Syncs",
    "03a": "Dependency review",
    "03b": "Data model",
    "04a": "Storage mapping",
    "04b": "SPEC",
    "04c": "Flow tests",
}


def main():
    parser = argparse.ArgumentParser(description="Present gate artefacts for human review")
    parser.add_argument("--feature", required=True, help="Feature root path (e.g. features/UC-XX-<slug>)")
    parser.add_argument("--gate", required=True, type=int, choices=[1, 2, 3], help="Gate number to present")
    args = parser.parse_args()

    feature_root = os.path.abspath(args.feature)
    gate_info = GATE_STAGES[args.gate]
    feature_name = os.path.basename(feature_root)

    print(f"=" * 60)
    print(f"  GATE {args.gate} — {gate_info['label']}")
    print(f"  Feature: {feature_name}")
    print(f"  {gate_info['description']}")
    print(f"=" * 60)
    print()

    all_ok = True
    for stage_id in gate_info["stages"]:
        stage_name = STAGE_NAMES.get(stage_id, stage_id)
        # Determine the output directory path
        if stage_id in ("01", "02a", "02b", "02", "03", "03a", "03b"):
            out_dir = os.path.join(feature_root, "stages", f"{stage_id}_{STAGE_NAMES.get(stage_id, stage_id).lower().replace(' ', '_')}", "output")
        elif stage_id.startswith("04"):
            sub = {"04a": "04a_storage-mapping", "04b": "04b_spec", "04c": "04c_flow-tests"}[stage_id]
            out_dir = os.path.join(feature_root, "stages", "04_implement", sub, "output")
        else:
            out_dir = os.path.join(feature_root, "stages", f"{stage_id}_", "output")

        # Try to find the actual output directory
        real_dirs = []
        for root, dirs, files in os.walk(os.path.join(feature_root, "stages")):
            if root.endswith("/output"):
                real_dirs.append(root)

        # Match by stage
        matching = [d for d in real_dirs if f"_{stage_id}" in d or f"/{stage_id}_" in d or f"0{stage_id}" in d]

        if not matching:
            # Try broader match
            for d in real_dirs:
                path_parts = d.split("/")
                for part in path_parts:
                    if stage_id in part:
                        matching.append(d)
                        break

        if matching:
            out_dir = matching[0]
            files = [f for f in os.listdir(out_dir) if f != ".gitkeep" and f != ".gitkeep.md" and not f.startswith(".")]
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
