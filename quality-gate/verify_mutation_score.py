#!/usr/bin/env python3
"""
verify_mutation_score.py — Stage gate: test effectiveness via mutation score.

Why this exists (DR-0001):
  In-loop red/green proved only that an agent ran a test, not that the test
  would catch a regression. The test-effectiveness gate is now the mutation
  score of the concept and sync unit suites: a suite that kills few mutants
  does not constrain the code. This script runs the profile's mutation tool
  and fails when the reported score is below `mutation.threshold`.

Configuration (repo-root `clad.properties`):
  mutation.command    shell command that runs the profile's mutation tool and
                      prints a final line `MUTATION_SCORE: <pct>` (or per-scope
                      `MUTATION_SCORE.concepts: <pct>` / `MUTATION_SCORE.syncs: <pct>`).
  mutation.threshold  minimum acceptable percentage (default 80).

The command is profile-specific; when `mutation.command` is unset the check
skips (a profile without a mutation tool relies on contract-outcome coverage
and field assertions instead).

Usage:
  python3 verify_mutation_score.py --feature-root features/UC-XX-<slug> \
    --scope concepts
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

import clad_stages as cs

_SCORE_RE_TMPL = r"MUTATION_SCORE(?:\.{scope})?:\s*([0-9]+(?:\.[0-9]+)?)"
_SKIP_RE = re.compile(r"MUTATION_SKIP:\s*(.+)")


def parse_score(output: str, scope: str) -> float | None:
    """Return the reported mutation percentage, preferring a scope-specific
    marker over the generic one. Last match wins (the tool prints a summary)."""
    scoped = re.findall(_SCORE_RE_TMPL.format(scope=re.escape(scope)), output,
                        re.IGNORECASE)
    if scoped:
        return float(scoped[-1])
    generic = re.findall(_SCORE_RE_TMPL.format(scope=""), output, re.IGNORECASE)
    return float(generic[-1]) if generic else None


def parse_skip(output: str) -> str | None:
    """Return the reason from the last `MUTATION_SKIP: <reason>` line."""
    matches = _SKIP_RE.findall(output)
    return matches[-1].strip() if matches else None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check the mutation score of a unit-test suite")
    parser.add_argument("--feature-root", required=True,
                        help="Feature root (e.g. features/UC-XX-<slug>)")
    parser.add_argument("--scope", default="concepts",
                        help="Scope label for a scope-specific score line")
    parser.add_argument("--require", action="store_true",
                        help="A SKIP (tool cannot run) is a failure, not a skip. "
                             "Use in CI so the gate cannot silently degrade.")
    args = parser.parse_args()

    feature_root = os.path.abspath(args.feature_root)
    command = cs.get_property(feature_root, "mutation.command")
    if not command:
        if args.require:
            print("FAIL  mutation gate is required but mutation.command is unset")
            return 1
        print("SKIP  mutation.command is not set — no mutation tool configured")
        return 0

    raw_threshold = cs.get_property(feature_root, "mutation.threshold") or "80"
    try:
        threshold = float(raw_threshold)
    except ValueError:
        print(f"FAIL  mutation.threshold is not a number: {raw_threshold!r}")
        return 1

    repo_root = os.path.dirname(os.path.dirname(feature_root))
    try:
        proc = subprocess.run(command, shell=True, cwd=repo_root,
                              capture_output=True, text=True)
    except OSError as exc:
        print(f"FAIL  could not run mutation.command: {exc}")
        return 1

    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    score = parse_score(combined, args.scope)
    if score is None:
        skip = parse_skip(combined)
        if skip is not None:
            if args.require:
                print(f"FAIL  mutation gate is required but skipped: {skip}")
                return 1
            print(f"SKIP  mutation gate skipped: {skip}")
            return 0
        print("FAIL  mutation.command ran but printed neither a "
              "`MUTATION_SCORE: <pct>` nor a `MUTATION_SKIP: <reason>` line.")
        tail = combined.strip().splitlines()[-5:]
        for line in tail:
            print(f"      | {line}")
        return 1

    if score < threshold:
        print(f"FAIL  mutation score {score:.1f}% < threshold "
              f"{threshold:.1f}% ({args.scope}). Strengthen the suite "
              f"(assertions that discriminate wrong behaviour), not the "
              f"count of tests.")
        return 1

    print(f"PASS  mutation score {score:.1f}% >= {threshold:.1f}% "
          f"({args.scope})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
