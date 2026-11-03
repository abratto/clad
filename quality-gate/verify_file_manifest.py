#!/usr/bin/env python3
"""
verify_file_manifest.py — Stage gate: output/ contains exactly the expected files.

Why this exists:
  Previously, an LLM had to manually check that every expected file was present
  in a stage's output/ directory — a non-deterministic step that frequently
  missed missing or extra files. This script makes the check deterministic:
  it compares the actual files against the expected list and exits non-zero
  if there's a mismatch.

Usage:
  python3 verify_file_manifest.py --dir <output-dir> --expected <file1,file2,...>

Exits 0 if every expected file exists and no unexpected file is present.
Ignored by construction: `.gitkeep` (a placeholder) and
`*-all-scenarios-chain.md` (a documented NON-canonical derived view the
generators already skip — see `examples/UC-00-login/README.md`).
Exits 1 with a report of mismatches.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_runner as cr  # noqa: E402


def main(argv=None) -> int:
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--dir", required=True,
                            help="Path to the output/ directory to inspect")
        parser.add_argument("--expected", required=True,
                            help="Comma-separated list of expected filenames "
                                 "(e.g. 'usecase.md' or 'User.contract.md,Session.contract.md')")

    def body(args: argparse.Namespace) -> cr.Verdict:
        out_dir = args.dir
        expected = set(args.expected.split(","))

        if not os.path.isdir(out_dir):
            return cr.Verdict.fail(f"directory not found: {out_dir}")

        actual = {
            f for f in os.listdir(out_dir)
            if not f.startswith(".") and not f.endswith("-all-scenarios-chain.md")
        }

        missing = expected - actual
        extra = actual - expected

        problems = []
        for f in sorted(missing):
            problems.append(cr.Problem(f"missing expected file: {f}"))
        for f in sorted(extra):
            problems.append(cr.Problem(f"unexpected file: {f}"))

        if problems:
            return cr.Verdict.fail("", problems)

        return cr.Verdict.ok(f"manifest matches ({len(expected)} files)")

    return cr.run_check(
        "Verify output/ contains exactly the expected files. "
        "Replaces non-deterministic LLM self-audit of file manifests.",
        body, argv, configure)


if __name__ == "__main__":
    sys.exit(main())
