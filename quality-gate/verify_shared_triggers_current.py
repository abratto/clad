#!/usr/bin/env python3
"""
verify_shared_triggers_current.py — the cross-UC shared-trigger view is current.

Why this exists:
  `features/_system/shared-triggers.md` is the advisory view that surfaces the
  cross-feature coordination defect the per-feature gates cannot see: two use
  cases firing a sync on the same concept-action completion (R11). It is
  generated, but nothing regenerated or checked it, so it went stale after the
  grammar-v3 re-sync — which is why UC-03 and UC-04 both bootstrapping
  `MemberEnrolment.verify` on different routes produced two identically-named
  rules that surfaced only at Stage 04e rather than at Stage 03a
  (maintenance/route-scoped-sync-names.md).

Usage:
  python3 verify_shared_triggers_current.py --features-dir features

Exit: 0 pass/skip, 1 stale.
"""

import argparse
import os
import sys

import generate_shared_triggers as gst


def _normalise(text):
    """Compare on logical content: normalise line endings and strip trailing
    whitespace per line, so a benign generator formatting change (EOL, trailing
    spaces) does not report false staleness."""
    return [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="The cross-UC shared-trigger view is up to date")
    parser.add_argument("--features-dir", default="features")
    args = parser.parse_args()

    features = os.path.abspath(args.features_dir)
    out_path = os.path.join(features, "_system", "shared-triggers.md")
    if not os.path.isfile(out_path):
        print("SKIP  no shared-trigger view (Not generated yet)")
        return 0

    with open(out_path, encoding="utf-8") as handle:
        current = handle.read()
    fresh = gst.render(features)

    if _normalise(current) != _normalise(fresh):
        print("FAIL  features/_system/shared-triggers.md is stale — it no "
              "longer matches the sync packs it indexes")
        print("      run: python3 quality-gate/generate_shared_triggers.py --write")
        return 1

    print("PASS  shared-trigger view is current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
