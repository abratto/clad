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

Exits 0 if every expected file exists and no unexpected file is present
(ignoring .gitkeep). Exits 1 with a report of mismatches.
"""

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Verify output/ contains exactly the expected files. "
                    "Replaces non-deterministic LLM self-audit of file manifests.")
    parser.add_argument("--dir", required=True,
                        help="Path to the output/ directory to inspect")
    parser.add_argument("--expected", required=True,
                        help="Comma-separated list of expected filenames "
                             "(e.g. 'usecase.md' or 'User.spec.md,Session.spec.md')")
    args = parser.parse_args()

    out_dir = args.dir
    expected = set(args.expected.split(","))

    if not os.path.isdir(out_dir):
        print(f"FAIL  directory not found: {out_dir}")
        sys.exit(1)

    actual = {f for f in os.listdir(out_dir)
              if f != ".gitkeep" and f != ".gitkeep.md"}

    missing = expected - actual
    extra = actual - expected

    passed = True
    if missing:
        for f in sorted(missing):
            print(f"FAIL  missing expected file: {f}")
        passed = False
    if extra:
        for f in sorted(extra):
            print(f"FAIL  unexpected file: {f}")
        passed = False

    if passed:
        print(f"PASS  manifest matches ({len(expected)} files)")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
