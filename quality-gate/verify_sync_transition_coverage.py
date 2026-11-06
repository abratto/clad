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

import check_runner as cr
import generate_syncs as gs
from verify_stage_sequence import APPROVED_STATES, gate_status


def main(argv=None) -> int:
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--feature", required=True, help="Feature root path")

    def body(args: argparse.Namespace) -> cr.Verdict:
        feature = os.path.abspath(args.feature)
        expected, _warnings = gs.derive_syncs_for_feature(feature)
        sync_dir = os.path.join(feature, "stages", "03_syncs", "output")

        present = {f[:-len(".sync.md")] for f in os.listdir(sync_dir)
                   if f.endswith(".sync.md")} if os.path.isdir(sync_dir) else set()
        missing = [g.stem for g in expected if g.stem not in present]
        if not missing:
            return cr.Verdict.ok(
                f"{len(expected)} derived chain transition(s) all present as "
                f"sync files")

        # Exact matching for a feature still being authored: a missing derived
        # stem is a missing transition, full stop. An unrelated `.sync.md` that
        # happens to make the count match must NOT satisfy coverage (finding:
        # "transition coverage can mistake an unrelated file for a missing
        # transition"). Only a frozen feature (Gate 3 approved) may carry legacy
        # hand-authored names, and even then a shortfall still fails.
        resume = os.path.join(feature, "RESUME.md")
        frozen = False
        if os.path.isfile(resume):
            with open(resume, encoding="utf-8", errors="replace") as fh:
                frozen = gate_status(fh.read(), 3) in APPROVED_STATES

        if frozen and len(present) >= len(expected):
            return cr.Verdict.ok(
                f"{len(expected)} chain transition(s) covered by {len(present)} "
                f"sync file(s) (frozen feature: legacy naming, counts agree)")

        verdict = cr.Verdict.fail(
            f"{len(missing)} chain transition(s) have no sync file "
            f"({len(present)} present of {len(expected)} derived)",
            [cr.Problem(f"missing: {stem}.sync.md") for stem in missing])
        verdict.detail = "      Derive/emit the missing carrier(s); do not advance."
        return verdict

    return cr.run_check(
        "Every chain-table transition must have a sync file",
        body, argv, configure)


if __name__ == "__main__":
    sys.exit(main())
