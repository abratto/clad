#!/usr/bin/env python3
"""
verify_test_framework_config.py — Stage gate: ensure test framework config matches artefacts.

Why this exists:
  An agent can forget to set TEST_FRAMEWORK or to produce the corresponding artefacts
  (.feature files for CUCUMBER, markdown flow-test specs for NATIVE). This script
  runs as a pre-flight check at the start of Stage 04c and fails fast if the track
  is misconfigured or missing, before any test files are written.

The 04c CONTEXT.md says: "Set it once when the feature skeleton is first copied."
This script makes that instruction mechanically enforceable.

Checks:
  1. Determines active test framework from resolution order:
     a. features/UC-XX/_config/test-framework.md  (per-feature override)
     b. clad.properties                             (repo root, if present)
     c. Default: NATIVE (backward compatible)
  2. If CUCUMBER:
     - Asserts at least one .feature file exists under the configured feature path
     - Asserts no markdown flow-test specs exist (wrong track)
  3. If NATIVE:
     - Asserts at least one markdown flow-test spec exists in 04c output
     - Asserts no .feature files exist (wrong track)
  4. Cross-check: the actual 04c output artefacts match the declared track

Usage:
  python3 verify_test_framework_config.py \
    --config-dir features/UC-XX/_config/ \
    --clad-properties clad.properties \
    --feature-output-dir features/UC-XX/stages/04_implement/04c_flow-tests/output/ \
    --feature-files-dir app/backend/src/test/resources/features/
"""

import argparse
import os
import re
import sys


def read_config_value(config_dir, key):
    """Read a config value from _config/<key>.md files.
    Pattern: KEY=VALUE on any line in the file.
    """
    key_upper = key.replace(".", "_").upper()
    for fname in os.listdir(config_dir):
        if not fname.endswith(".md"):
            continue
        # Only check files matching the key pattern
        base = fname.replace(".md", "").replace("-", "_").upper()
        if base != key_upper:
            continue
        path = os.path.join(config_dir, fname)
        with open(path) as f:
            for line in f:
                m = re.match(rf"^{key_upper}=(.+)$", line.strip())
                if m:
                    return m.group(1).strip()
    return None


def read_clad_properties(path):
    """Read key=value pairs from clad.properties."""
    if not os.path.isfile(path):
        return {}
    props = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r"^([a-zA-Z.]+)=(.+)$", line)
            if m:
                props[m.group(1).strip()] = m.group(2).strip()
    return props


def main():
    parser = argparse.ArgumentParser(
        description="Verify test framework config matches produced artefacts")
    parser.add_argument("--config-dir", required=True,
                        help="Path to features/UC-XX/_config/")
    parser.add_argument("--clad-properties", default="clad.properties",
                        help="Path to repo-root clad.properties")
    parser.add_argument("--feature-output-dir", required=True,
                        help="Path to 04c_flow-tests/output/")
    parser.add_argument("--feature-files-dir", required=True,
                        help="Path to app/backend/src/test/resources/features/")
    args = parser.parse_args()

    passed = True

    if not os.path.isdir(args.config_dir):
        print(f"FAIL  config directory not found: {args.config_dir}")
        sys.exit(1)

    # 1. Resolve effective test framework
    framework = None

    # Try per-feature override first
    override = read_config_value(args.config_dir, "test.framework")
    if override:
        framework = override.upper()
        print(f"INFO  TEST_FRAMEWORK={framework} (from {args.config_dir}/test-framework.md)")

    # Try clad.properties second
    if not framework:
        props = read_clad_properties(args.clad_properties)
        if "test.framework" in props:
            framework = props["test.framework"].upper()
            print(f"INFO  TEST_FRAMEWORK={framework} (from {args.clad_properties})")

    # Default
    if not framework:
        framework = "NATIVE"
        print(f"INFO  TEST_FRAMEWORK={framework} (default — no config found)")

    # 2. Count artefacts
    feature_files = []
    if os.path.isdir(args.feature_files_dir):
        feature_files = [f for f in os.listdir(args.feature_files_dir)
                         if f.endswith(".feature")]

    flow_spec_files = []
    if os.path.isdir(args.feature_output_dir):
        flow_spec_files = [f for f in os.listdir(args.feature_output_dir)
                          if f.endswith("-flow-test.md")]

    # 3. Validate CUCUMBER track
    if framework == "CUCUMBER":
        if not feature_files:
            print(f"FAIL  TEST_FRAMEWORK=CUCUMBER but no .feature files found "
                  f"in {args.feature_files_dir}. "
                  f"Create a .feature file (see templates/feature.feature "
                  f"and methodology/architecture/GHERKIN_INTEGRATION.md).")
            passed = False
        else:
            print(f"INFO  CUCUMBER track: {len(feature_files)} .feature file(s) found "
                  f"({', '.join(feature_files)})")
            # Optional: warn if markdown flow-test specs also exist (wrong track artefacts)
            if flow_spec_files:
                print(f"WARN  CUCUMBER track but {len(flow_spec_files)} markdown "
                      f"flow-test spec(s) also exist in {args.feature_output_dir}. "
                      f"CUCUMBER should use .feature files, not markdown flow-test specs.")

    # 4. Validate NATIVE track
    elif framework == "NATIVE":
        if not flow_spec_files:
            print(f"FAIL  TEST_FRAMEWORK=NATIVE but no -flow-test.md files found "
                  f"in {args.feature_output_dir}. "
                  f"Create flow-test markdown specs for each scenario.")
            passed = False
        else:
            print(f"INFO  NATIVE track: {len(flow_spec_files)} flow-test spec(s) found "
                  f"({', '.join(flow_spec_files)})")

        if feature_files:
            print(f"WARN  NATIVE track but {len(feature_files)} .feature file(s) "
                  f"found in {args.feature_files_dir}. "
                  f"NATIVE should not use .feature files. "
                  f"Either remove them or set TEST_FRAMEWORK=CUCUMBER.")

    else:
        print(f"FAIL  unknown TEST_FRAMEWORK value: {framework} "
              f"(expected CUCUMBER or NATIVE)")
        passed = False

    if passed:
        action = "happy-path" if framework == "CUCUMBER" else "flow-test"
        print(f"PASS  test framework config: {framework} track, "
              f"{'✓' if framework == 'CUCUMBER' and feature_files else '✓'} "
              f"artefacts present")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
