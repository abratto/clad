#!/usr/bin/env python3
"""
verify_feature_file_presence.py — Stage gate: ensure .feature files exist for Stage 04c.

Why this exists:
  Stage 04c requires a Gherkin .feature file per use-case scenario. An agent can
  forget to produce one. This script runs as a pre-flight check at the start of
  Stage 04c and fails fast if the feature file is missing, before any test stubs
  are written.

Checks:
  1. At least one .feature file exists in the 04c output directory.
  2. That .feature file also exists in the Cucumber discovery path
     (src/test/resources/features/).

Usage:
  python3 verify_feature_file_presence.py \
    --feature-output-dir <04c_flow-tests/output/> \
    --feature-files-dir <src/test/resources/features/>
"""

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Verify .feature files exist for Stage 04c")
    parser.add_argument("--feature-output-dir", required=True,
                        help="Path to 04c_flow-tests/output/")
    parser.add_argument("--feature-files-dir", required=True,
                        help="Path to src/test/resources/features/")
    args = parser.parse_args()

    passed = True

    # Check 04c output directory
    output_files = []
    if os.path.isdir(args.feature_output_dir):
        output_files = [f for f in os.listdir(args.feature_output_dir)
                        if f.endswith(".feature")]
    else:
        print(f"FAIL  output directory not found: {args.feature_output_dir}")
        passed = False

    # Check Cucumber discovery path
    discovery_files = []
    if os.path.isdir(args.feature_files_dir):
        discovery_files = [f for f in os.listdir(args.feature_files_dir)
                           if f.endswith(".feature")]
    else:
        print(f"FAIL  feature files directory not found: {args.feature_files_dir}")
        passed = False

    # Assert .feature files exist in output
    if not output_files:
        print(f"FAIL  no .feature files found in {args.feature_output_dir}. "
              f"Create a .feature file (see templates/feature.feature "
              f"and methodology/architecture/GHERKIN_INTEGRATION.md).")
        passed = False
    else:
        print(f"INFO  {len(output_files)} .feature file(s) in output: "
              f"{', '.join(output_files)}")

    # Assert .feature files exist in Cucumber discovery path
    if not discovery_files:
        print(f"FAIL  no .feature files found in {args.feature_files_dir}. "
              f"Copy the .feature file to the Cucumber discovery path.")
        passed = False
    else:
        print(f"INFO  {len(discovery_files)} .feature file(s) in discovery path: "
              f"{', '.join(discovery_files)}")

    # Verify cross-copy: every output file should exist in discovery path
    for fname in output_files:
        if fname not in discovery_files:
            print(f"WARN  {fname} exists in output but not in {args.feature_files_dir}. "
                  f"Copy it to the Cucumber discovery path.")

    if passed:
        print(f"PASS  feature file presence check: {len(output_files)} file(s) present")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
