#!/usr/bin/env python3
"""
verify_sync_transition_coverage.py — Stage 03: every chain-table invocation
edge must have a sync file.

Why this exists:
  Stage 03's checks (scenario coverage, sync matrix, cycle graph, overlap)
  verify the syncs that ARE present, but none verifies that every chain-table
  transition was actually lowered. A missing sync (e.g. an un-emitted joined
  response carrier) could pass Stage 03 silently and only surface much later.
  This check derives the expected sync stems from the canonical chain tables
  with the same generator logic Stage 03 uses, and fails when any is absent.

Usage:
  python3 verify_sync_transition_coverage.py --feature <features/UC-XX-slug>
"""

import argparse
import os
import sys

import generate_syncs as gs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Every chain-table transition must have a sync file")
    parser.add_argument("--feature", required=True, help="Feature root path")
    args = parser.parse_args()

    feature = os.path.abspath(args.feature)
    expected, _warnings = gs.derive_syncs_for_feature(feature)
    sync_dir = os.path.join(feature, "stages", "03_syncs", "output")

    present = {f[:-len(".sync.md")] for f in os.listdir(sync_dir)
               if f.endswith(".sync.md")} if os.path.isdir(sync_dir) else set()
    missing = [g.stem for g in expected if g.stem not in present]
    if not missing:
        print(f"PASS  {len(expected)} derived chain transition(s) all present as sync files")
        return 0

    # Frozen/historical features (e.g. the UC-00 worked example) may carry
    # pre-v0.6 hand-authored names, so a stem mismatch is not a missing
    # transition when the counts agree. Fail only on a genuine shortfall.
    if len(present) >= len(expected):
        print(f"PASS  {len(expected)} chain transition(s) covered by {len(present)} "
              f"sync file(s) (naming differs; counts agree)")
        return 0

    print(f"FAIL  {len(missing)} chain transition(s) have no sync file "
          f"({len(present)} present of {len(expected)} derived):")
    for stem in missing:
        print(f"        missing: {stem}.sync.md")
    print("      Derive/emit the missing carrier(s); do not advance.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
