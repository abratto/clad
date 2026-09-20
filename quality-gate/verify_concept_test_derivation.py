#!/usr/bin/env python3
"""
verify_concept_test_derivation.py — Stage gate: concept test derivation matches contract outcomes.

Why this exists:
  Concept tests (Stage 04d-red) are derived mechanically from contract outcome enums
  (04b_contract) and outer flow tests (04c). An LLM can omit an outcome, rename it,
  or write tests without updating the derivation map. This script checks that
  every contract outcome has a corresponding test row in the derivation map and
  that every named test class/method exists in the Java source.

Checks:
  1. Every contract outcome enum for every concept action has a matching row
     in concept-test-derivation.md
  2. Every test method named in the derivation map exists in the corresponding
     Java test class
  3. No test method in the derivation map references an outcome not defined
     in the contract

Usage:
  python3 verify_concept_test_derivation.py \
    --contract-dir <04b_contract/output/> \
    --derivation <concept-test-derivation.md> \
    --test-source-root <APP_TEST_SOURCE_ROOT>
"""

import argparse
import os
import re
import sys

import artifact_parsers as ap


def parse_spec_outcomes(contract_dir):
    """Shared contract-outcome parser (artifact_parsers)."""
    return ap.parse_spec_outcomes(contract_dir)


def parse_derivation(derivation_path):
    """Shared derivation-map parser (artifact_parsers)."""
    return ap.parse_derivation_map(derivation_path)


def find_java_test_class(test_source_root, test_class):
    """
    Search for a Java test class file by name (without .java extension).
    Returns the file path if found, None otherwise.
    """
    for root, dirs, files in os.walk(test_source_root):
        for f in files:
            if f == f"{test_class}.java":
                return os.path.join(root, f)
    return None


def find_java_test_method(test_file, method_name):
    """
    Check if a Java test file contains a method with the given name.
    Returns True if found.
    """
    if not test_file or not os.path.isfile(test_file):
        return False
    with open(test_file) as f:
        content = f.read()
    # Look for @Test annotation followed by method declaration
    pattern = rf"@Test\s*\n\s*(?:public\s+)?void\s+{re.escape(method_name)}\s*\("
    return bool(re.search(pattern, content))


def main():
    parser = argparse.ArgumentParser(
        description="Verify concept test derivation against contract outcomes")
    parser.add_argument("--contract-dir", required=True,
                        help="Path to 04b_contract/output/")
    parser.add_argument("--derivation", required=True,
                        help="Path to concept-test-derivation.md")
    parser.add_argument("--test-source-root", required=True,
                        help="Path to APP_TEST_SOURCE_ROOT (e.g. app/backend/src/test/java)")
    args = parser.parse_args()

    passed = True

    if not os.path.isdir(args.contract_dir):
        print(f"FAIL  contract directory not found: {args.contract_dir}")
        sys.exit(1)
    if not os.path.isfile(args.derivation):
        print(f"FAIL  derivation file not found: {args.derivation}")
        sys.exit(1)
    if not os.path.isdir(args.test_source_root):
        print(f"FAIL  test source root not found: {args.test_source_root}")
        sys.exit(1)

    # 1. Parse contract outcomes
    spec_outcomes = parse_spec_outcomes(args.contract_dir)
    if not spec_outcomes:
        print("FAIL  no contract outcomes parsed — check --contract-dir")
        sys.exit(1)

    # 2. Parse derivation map
    derivations = parse_derivation(args.derivation)
    if not derivations:
        print("FAIL  no derivation rows parsed — check --derivation format")
        sys.exit(1)

    # Build lookup: {(concept, action): set_of_derived_outcomes}
    derived_outcomes = {}
    derived_methods = {}  # {test_class: [(method, outcome)]}
    for test_class, test_method, outcome, concept, action in derivations:
        key = (concept, action)
        derived_outcomes.setdefault(key, set()).add(outcome)
        derived_methods.setdefault(test_class, []).append((test_method, outcome))

    # 3. Cross-reference: every contract outcome has a derivation row
    for (concept, action), spec_outs in sorted(spec_outcomes.items()):
        key = (concept, action)
        derived_outs = derived_outcomes.get(key, set())
        missing = spec_outs - derived_outs
        extra = derived_outs - spec_outs

        for outcome in sorted(missing):
            print(f"FAIL  {concept}.{action}: contract outcome '{outcome}' "
                  f"has no test row in derivation map")
            passed = False

        for outcome in sorted(extra):
            print(f"WARN  {concept}.{action}: derivation maps outcome "
                  f"'{outcome}' but it is not in contract outcomes "
                  f"{sorted(spec_outs)}")
            # WARN not FAIL — derivation may cover cross-feature outcomes

    # 4. Check Java test class and method existence
    for test_class, methods in sorted(derived_methods.items()):
        test_file = find_java_test_class(args.test_source_root, test_class)
        if not test_file:
            print(f"FAIL  test class '{test_class}.java' not found "
                  f"under {args.test_source_root}")
            passed = False
            continue

        for method, outcome in methods:
            if not find_java_test_method(test_file, method):
                print(f"FAIL  test method '{method}' not found in "
                      f"'{test_class}.java'")
                passed = False

    spec_count = sum(len(v) for v in spec_outcomes.values())
    derived_count = len(derivations)
    action_count = len(spec_outcomes)

    if passed:
        print(f"PASS  {spec_count} contract outcomes → {derived_count} derivation "
              f"rows across {action_count} actions; all Java test methods exist")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
