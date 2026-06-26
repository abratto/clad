#!/usr/bin/env python3
"""
verify_test_naming.py — Stage gate: London School test naming conventions.

Why this exists:
  Concept and sync unit tests (Stages 04d and 04e) must follow London School
  BDD naming conventions. An LLM can invent arbitrary method names that drift
  from the convention. This script checks for compliance deterministically.

Checks:
  1. Class name follows <Concept><Action>Test or <SyncName>Test pattern
  2. Every @Test method name starts with 'should'
  3. At least one @Nested class exists (unless only one test method)
  4. // GIVEN, // WHEN, // THEN comments appear in each test method body

Usage:
  python3 verify_test_naming.py \
    --test-source-root <path> \
    --scope concepts,syncs
"""

import argparse
import os
import re
import sys


CLASS_NAME_RE = re.compile(
    r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+Test)', re.MULTILINE)
NESTED_RE = re.compile(r'@Nested.*?\n\s*(?:@\w+(?:\([^)]*\))?\s*\n\s*)*class\s+(\w+)', re.DOTALL)
TEST_METHOD_RE = re.compile(r'@Test\s+(?:@DisplayName.*\n\s*)?\n?\s*(?:public\s+)?void\s+(\w+)')
DISABLED_RE = re.compile(r'@Disabled[(\n]')
GIVEN_RE = re.compile(r'//\s*GIVEN', re.IGNORECASE)
WHEN_RE = re.compile(r'//\s*WHEN', re.IGNORECASE)
THEN_RE = re.compile(r'//\s*THEN', re.IGNORECASE)
CONCEPT_TEST_RE = re.compile(r'(\w+)Test')
PACKAGE_RE = re.compile(r'package\s+([\w.]+);')
ACTION_LINE_RE = re.compile(r'\*:\s+(\w+)\.(\w+)')
CONCEPT_PACKAGE_RE = re.compile(r'concepts\.(\w+)')


def find_java_files(root, package_names):
    """Walk source root for test Java files under the given packages."""
    files = []
    if not os.path.isdir(root):
        return files
    for dirpath, dirnames, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith('Test.java') and not fname.endswith('Base.java'):
                full = os.path.join(dirpath, fname)
                for pkg in package_names:
                    marker = os.sep + pkg + os.sep
                    if marker in full:
                        files.append(full)
                        break
    return sorted(files)


def scan_file(filepath):
    """Extract class name, @Nested classes, @Test methods, and comment
    presence from a Java test file."""
    with open(filepath) as f:
        content = f.read()

    # Skip @Disabled test classes entirely (stubs waiting for later stages)
    if re.search(r'@Disabled[(\n]', content):
        return None

    class_match = CLASS_NAME_RE.search(content)
    if not class_match:
        return None
    class_name = class_match.group(1)

    nested = [m.group(1) for m in NESTED_RE.finditer(content)]

    methods = []
    for tm in TEST_METHOD_RE.finditer(content):
        method_name = tm.group(1)
        if method_name == 'setUpEngine':
            continue  # skip the test base setUp
        # Find the method body — everything from the method to the next
        # @Test, @BeforeEach, @AfterEach, class, or end of file
        start = tm.end()
        body_end = len(content)
        for marker in ['@Test', '@BeforeEach', '@AfterEach', '@Nested',
                         'class ', 'interface ']:
            idx = content.find(marker, start)
            if idx != -1 and idx < body_end:
                body_end = idx
        body = content[start:body_end]
        methods.append({
            'name': method_name,
            'has_given': bool(GIVEN_RE.search(body)),
            'has_when': bool(WHEN_RE.search(body)),
            'has_then': bool(THEN_RE.search(body)),
        })

    # Determine scope from package
    pkg_match = PACKAGE_RE.search(content)
    pkg = pkg_match.group(1) if pkg_match else ''
    is_sync = '.syncs' in pkg
    is_concept = '.concepts.' in pkg

    return {
        'file': filepath,
        'class_name': class_name,
        'nested': nested,
        'methods': methods,
        'is_sync': is_sync,
        'is_concept': is_concept,
        'package': pkg,
    }


def check_conventions(filepath, info):
    """Return list of violation messages, or empty list if all rules pass."""
    violations = []
    class_name = info['class_name']
    methods = info['methods']
    nested = info['nested']
    is_sync = info['is_sync']
    is_concept = info['is_concept']

    if not methods:
        violations.append(f"  No @Test methods found in {class_name}")
        return violations

    # R1: Class naming
    if is_concept:
        # <Concept><Action>Test pattern — class name must have 3+ uppercase
        # segments (Concept, Action, Test) and CamelCase
        parts = re.findall(r'[A-Z][a-z0-9]*', class_name)
        if len(parts) < 2 or parts[-1] != 'Test':
            violations.append(
                f"  {class_name}: should follow <Concept><Action>Test pattern\n"
                f"    e.g. 'UserLookupByUsernameTest' (got '{class_name}')")
    elif is_sync:
        if not class_name.endswith('Test'):
            violations.append(
                f"  {class_name}: should end with 'Test' (sync test naming)")

    # R2: Every @Test method starts with 'should'
    for m in methods:
        if not m['name'].startswith('should'):
            violations.append(
                f"  {class_name}.{m['name']}(): should use 'should<X>When<Y>' prefix")

    # R3: @Nested class presence (skip if only 1 test method)
    if len(methods) > 1 and not nested:
        violations.append(
            f"  {class_name}: missing @Nested class(es) — "
            f"group {len(methods)} test methods by precondition")

    # R4: Given-When-Then comments
    for m in methods:
        missing = []
        if not m['has_given']:
            missing.append('// GIVEN')
        if not m['has_when']:
            missing.append('// WHEN')
        if not m['has_then']:
            missing.append('// THEN')
        if missing:
            violations.append(
                f"  {class_name}.{m['name']}(): missing {', '.join(missing)} comments")

    return violations


def main():
    parser = argparse.ArgumentParser(
        description="Verify London School test naming conventions")
    parser.add_argument("--test-source-root", required=True,
                        help="Path to the test source root (e.g. ref-impl/.../test/java)")
    parser.add_argument("--scope", default="concepts,syncs",
                        help="Comma-separated list of package dirs to check (default: concepts,syncs)")
    args = parser.parse_args()

    packages = [p.strip() for p in args.scope.split(",") if p.strip()]

    files = find_java_files(args.test_source_root, packages)

    if not files:
        print(f"WARN  No test files found under {args.test_source_root} "
              f"for packages: {packages}")
        print("      (No concept or sync unit tests exist yet — "
              "this is expected if 04d/04e have not been run.)")
        return 0

    print(f"verify_test_naming.py: {len(files)} test file(s) "
          f"under {packages}")

    all_pass = True
    file_count = 0
    method_count = 0

    for f in files:
        info = scan_file(f)
        if info is None:
            continue
        file_count += 1
        method_count += len(info['methods'])
        violations = check_conventions(f, info)

        if violations:
            all_pass = False
            print(f"  ✗ {info['class_name']} — {len(violations)} violation(s)")
            for v in violations:
                print(v)
        else:
            nested_info = (
                f", @Nested present ({', '.join(info['nested'])})"
                if info['nested'] else "")
            print(f"  ✓ {info['class_name']} — "
                  f"{len(info['methods'])} method(s), "
                  f"all should-prefixed{nested_info}")

    print(
        f"{'All' if all_pass else 'Some'} test naming conventions {'pass' if all_pass else 'fail'}.")

    if not all_pass:
        total = 0
        for f in files:
            info = scan_file(f)
            if info and check_conventions(f, info):
                total += len(check_conventions(f, info))
        print(f"\n{total} total violation(s). "
              "See above for details.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
