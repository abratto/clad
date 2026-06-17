#!/usr/bin/env python3
"""
verify_file_manifest.py — Stage gate: output/ contains exactly the expected files.

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
        description="Verify output/ contains exactly the expected files.")
    parser.add_argument("--dir", required=True,
                        help="Path to the output/ directory")
    parser.add_argument("--expected", required=True,
                        help="Comma-separated list of expected filenames")
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
