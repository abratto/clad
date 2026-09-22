#!/usr/bin/env python3
"""
verify_governance_hygiene.py — advisory: governance records do not go stale.

Why this exists:
  The readiness guards (`verify_iterative_change_readiness.py`,
  `verify_maintenance_change_readiness.py`) only run when their scope is
  touched, so a finished change whose record was never marked `closed` — or a
  `_changes/` record left `active` on a feature that is already complete — sits
  invisible until the *next* change trips over it. Twice in the Model B work a
  stale `active` record blocked or misled a later change.

This check is **advisory** (exit 0 always): it prints WARN lines for a human to
clear, never blocks a gate. Checks:

  * more than one `active` record under `maintenance/` — only one in-flight
    platform change at a time;
  * more than one `active` `_changes/` record under one feature — the readiness
    guard selects exactly one;
  * any `active` `_changes/` record on a feature whose RESUME says it is
    `feature complete` — a finished feature has no in-flight change.

Usage:
  python3 verify_governance_hygiene.py --features-dir features \
      --maintenance-dir maintenance
"""

import argparse
import os
import re
import sys

ACTIVE = re.compile(r"^-\s*\*\*Status:\*\*\s*`active`", re.MULTILINE)
FEATURE_COMPLETE = re.compile(r"feature complete", re.IGNORECASE)


def is_active(path):
    with open(path, encoding="utf-8") as handle:
        return bool(ACTIVE.search(handle.read()))


def active_markdown(directory):
    if not os.path.isdir(directory):
        return []
    return sorted(os.path.join(directory, name)
                  for name in os.listdir(directory)
                  if name.endswith(".md") and is_active(os.path.join(directory, name)))


def main() -> int:
    parser = argparse.ArgumentParser(description="Advisory governance-hygiene check")
    parser.add_argument("--features-dir", default="features")
    parser.add_argument("--maintenance-dir", default="maintenance")
    args = parser.parse_args()

    warnings = []

    maintenance = active_markdown(args.maintenance_dir)
    if len(maintenance) > 1:
        warnings.append(
            f"{len(maintenance)} `active` maintenance records — only one in-flight "
            f"change at a time; mark the finished ones `closed`: "
            + ", ".join(os.path.basename(p) for p in maintenance))

    if os.path.isdir(args.features_dir):
        for feature in sorted(os.listdir(args.features_dir)):
            root = os.path.join(args.features_dir, feature)
            changes_dir = os.path.join(root, "_changes")
            if not os.path.isdir(changes_dir):
                continue
            active = active_markdown(changes_dir)
            if not active:
                continue
            if len(active) > 1:
                warnings.append(
                    f"{feature}: {len(active)} `active` _changes/ records — the "
                    f"readiness guard selects exactly one: "
                    + ", ".join(os.path.basename(p) for p in active))
            resume = os.path.join(root, "RESUME.md")
            if os.path.isfile(resume):
                with open(resume, encoding="utf-8") as handle:
                    if FEATURE_COMPLETE.search(handle.read()):
                        warnings.append(
                            f"{feature}: `feature complete` but still carries an "
                            f"`active` _changes/ record "
                            f"({', '.join(os.path.basename(p) for p in active)}) "
                            f"— mark it `closed`")

    if warnings:
        print(f"WARN  governance hygiene: {len(warnings)} stale record(s)")
        for warning in warnings:
            print(f"  - {warning}")
        return 0

    print("PASS  governance records are current (no stale `active` records)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
