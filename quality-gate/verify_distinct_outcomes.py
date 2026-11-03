#!/usr/bin/env python3
"""verify_distinct_outcomes.py — one completion token must not fan out to two
distinct terminal responses.

Why this exists:
  Two behaviourally-distinct refusals (blank name -> 400, duplicate reference ->
  409) that share ONE completion token (`enrol[Refused]`) collapse two contracts
  into one node: the runtime cannot tell them apart, so `Web.respond` cannot pick
  a status, and R9/R12 (every contract outcome maps to a distinct branch) are
  violated. The v0.13.0 experiment met exactly this and had to split the request
  validation into pure guard actions (experiment defect D3).

  The fix is structural: model each request-level refusal as its own pure guard
  action with its own outcome, decided before the first state write (R23), so
  each terminal response has a distinct trigger token.

Detection: within one chain file, if a single `When` token (normalized
`Concept/action[Outcome]`) is the trigger of two or more terminal `Web.respond`
rows with DIFFERENT statuses, the responses are collapsed.

Usage:
  python3 verify_distinct_outcomes.py --chain-dir features/UC-XX-.../01b.../output
Exit: 0 pass/skip, 1 a collapsed branch.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifact_parsers as ap  # noqa: E402
import check_runner as cr  # noqa: E402


def _when_key(when: str) -> str:
    return re.sub(r"\s+", "", (when or "").strip().strip("`"))


def main(argv=None) -> int:
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--chain-dir", required=True)

    def body(args: argparse.Namespace) -> cr.Verdict:
        if not os.path.isdir(args.chain_dir):
            return cr.Verdict.skip("no chain-table directory")

        failures = []
        for filename in sorted(os.listdir(args.chain_dir)):
            if not filename.endswith("-chain.md"):
                continue
            path = os.path.join(args.chain_dir, filename)
            branches: dict[str, dict[int, int]] = {}
            for row in ap.parse_chain_table(path):
                if row.then_suffix is None or row.then_concept != "Web":
                    continue
                digits = re.search(r"\d+", row.then_suffix or "")
                if not digits or row.composite_when:
                    continue
                key = _when_key(row.when)
                branches.setdefault(key, {})[int(digits.group(0))] = row.row_num
            for key, statuses in sorted(branches.items()):
                if len(statuses) > 1:
                    failures.append(cr.Problem(
                        f"`{key}` -> statuses {sorted(statuses)}",
                        where=filename))

        if failures:
            verdict = cr.Verdict.fail(
                f"{len(failures)} collapsed branch(es): one completion token "
                f"reaches two distinct terminal responses", failures)
            verdict.detail = (
                "      Split each request-level refusal into its own pure guard "
                "action with its own outcome\n"
                "      before the first state write (R23), so each response has a "
                "distinct trigger token (R9/R12).")
            return verdict
        return cr.Verdict.ok("every terminal response has a distinct trigger token")

    return cr.run_check(
        "Distinct terminal responses need distinct trigger tokens",
        body, argv, configure)


if __name__ == "__main__":
    sys.exit(main())
