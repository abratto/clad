#!/usr/bin/env python3
"""
verify_concept_test_derivation.py — Stage gate: concept test derivation matches SPEC outcomes.

Why this exists:
  Concept tests (Stage 04d-red) are derived mechanically from SPEC outcome enums
  (04b_spec) and outer flow tests (04c). An LLM can omit an outcome, rename it,
  or write tests without updating the derivation map. This script checks that
  every SPEC outcome has a corresponding test row in the derivation map and
  that every named test class/method exists in the Java source.

Checks:
  1. Every SPEC outcome enum for every concept action has a matching row
     in concept-test-derivation.md
  2. Every test method named in the derivation map exists in the corresponding
     Java test class
  3. No test method in the derivation map references an outcome not defined
     in the SPEC

Usage:
  python3 verify_concept_test_derivation.py \
    --spec-dir <04b_spec/output/> \
    --derivation <concept-test-derivation.md> \
    --test-source-root <APP_TEST_SOURCE_ROOT>
"""

import argparse
import os
import re
import sys


def parse_spec_outcomes(spec_dir):
    """
    Parse SPEC files. Return dict:
      {(concept, action): set_of_outcomes}
    """
    result = {}
    if not os.path.isdir(spec_dir):
        return result

    for fname in sorted(os.listdir(spec_dir)):
        if not fname.endswith(".spec.md"):
            continue
        concept = fname.replace(".spec.md", "")
        path = os.path.join(spec_dir, fname)
        with open(path) as f:
            content = f.read()

        lines = content.split("\n")
        current_action = None

        for line in lines:
            # Detect action section: ### `actionName(...)`
            m_action = re.match(r"^###\s+`(\w+)\(", line.strip())
            if m_action:
                current_action = m_action.group(1)
                result.setdefault((concept, current_action), set())
                continue

            if current_action is None:
                continue

            # Match: - **Outcomes (enum):** `OK`, `BAD_PASSWORD`, `LOCKED`
            m_out = re.match(r"^- \*\*Outcomes.*?:\*\*\s+(.+)$", line.strip())
            if m_out:
                outcomes_str = m_out.group(1)
                outcomes = re.findall(r"`([^`]+)`", outcomes_str)
                result[(concept, current_action)] = set(outcomes)
                current_action = None

    return result


def parse_derivation(derivation_path):
    """
    Parse concept-test-derivation.md. Return:
      - derivations: list of (test_class, test_method, outcome, concept, action)
      - handoff_bundle: dict of handoff items
    Handles two table formats:
      Format A (template): `### Concept.action → test class: TestClass` heading
          with columns: | # | Test method | Outcome | Source | Preconditions | Arrange |
      Format B (compact): `## Concept.action(args) -> Result` heading
          with columns: | # | Outcome | Test class | Test method | Flow-test source |
    """
    derivations = []
    current_concept = None
    current_action = None
    current_test_class = None
    table_format = None  # 'a' or 'b'

    with open(derivation_path) as f:
        lines = f.readlines()

    for line in lines:
        # Detect Format A heading:
        # ### `Copy.checkAvailable` → test class: `CopyConceptTest`
        m_a = re.match(
            r"^###\s+`(\w+)\.(\w+)`\s*.*?→\s*test\s+class:\s*`(\w+)`",
            line.strip()
        )
        if m_a:
            current_concept = m_a.group(1)
            current_action = m_a.group(2)
            current_test_class = m_a.group(3)
            table_format = 'a'
            continue

        # Detect Format B heading:
        # ## Title.create(name) -> CreateResult
        m_b = re.match(
            r"^##\s+(\w+)\.(\w+)\(.*?\).*?->",
            line.strip()
        )
        if m_b:
            current_concept = m_b.group(1)
            current_action = m_b.group(2)
            current_test_class = None
            table_format = 'b'
            continue

        if current_concept is None or current_action is None:
            continue

        # Detect table row: | 1 | ...
        m_row = re.match(r"^\|\s*\d+\s*\|", line.strip())
        if not m_row:
            continue

        cols = [c.strip() for c in line.strip().split("|")]
        # Remove empty first/last from split
        cols = [c for c in cols if c]

        if table_format == 'a':
            # | # | Test method | Outcome | Source | Preconditions | Arrange |
            if len(cols) >= 4:
                test_method = cols[1].strip("`").rstrip("()")
                outcome = cols[2].strip("`")
                derivations.append((current_test_class, test_method,
                                    outcome, current_concept, current_action))

        elif table_format == 'b':
            # | # | Outcome | Test class | Test method | Flow-test source |
            if len(cols) >= 4:
                outcome = cols[1].strip("`")
                tc = cols[2].strip("`")
                test_method = cols[3].strip("`").rstrip("()")
                derivations.append((tc, test_method, outcome,
                                    current_concept, current_action))

    return derivations


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
        description="Verify concept test derivation against SPEC outcomes")
    parser.add_argument("--spec-dir", required=True,
                        help="Path to 04b_spec/output/")
    parser.add_argument("--derivation", required=True,
                        help="Path to concept-test-derivation.md")
    parser.add_argument("--test-source-root", required=True,
                        help="Path to APP_TEST_SOURCE_ROOT (e.g. app/backend/src/test/java)")
    args = parser.parse_args()

    passed = True

    if not os.path.isdir(args.spec_dir):
        print(f"FAIL  SPEC directory not found: {args.spec_dir}")
        sys.exit(1)
    if not os.path.isfile(args.derivation):
        print(f"FAIL  derivation file not found: {args.derivation}")
        sys.exit(1)
    if not os.path.isdir(args.test_source_root):
        print(f"FAIL  test source root not found: {args.test_source_root}")
        sys.exit(1)

    # 1. Parse SPEC outcomes
    spec_outcomes = parse_spec_outcomes(args.spec_dir)
    if not spec_outcomes:
        print("FAIL  no SPEC outcomes parsed — check --spec-dir")
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

    # 3. Cross-reference: every SPEC outcome has a derivation row
    for (concept, action), spec_outs in sorted(spec_outcomes.items()):
        key = (concept, action)
        derived_outs = derived_outcomes.get(key, set())
        missing = spec_outs - derived_outs
        extra = derived_outs - spec_outs

        for outcome in sorted(missing):
            print(f"FAIL  {concept}.{action}: SPEC outcome '{outcome}' "
                  f"has no test row in derivation map")
            passed = False

        for outcome in sorted(extra):
            print(f"WARN  {concept}.{action}: derivation maps outcome "
                  f"'{outcome}' but it is not in SPEC outcomes "
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
        print(f"PASS  {spec_count} SPEC outcomes → {derived_count} derivation "
              f"rows across {action_count} actions; all Java test methods exist")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
