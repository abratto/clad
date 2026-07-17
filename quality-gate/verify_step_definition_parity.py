#!/usr/bin/env python3
"""
verify_step_definition_parity.py — Stage gate: every Gherkin step has a
non-stub step-definition method.

Why this exists:
  Stage 04c produces .feature files and step-definition stubs (the outer red).
  An agent can write stub methods with empty bodies ({}), and the compilation
  check passes because syntax is valid. But empty stubs are NOT valid red tests
  — every step definition must have an actual implementation that exercises the
  application. This script catches empty-stub methods BEFORE the gate, so the
  agent doesn't advance with non-functional tests.

Checks:
  1. Every Given/When/Then step in every deployed .feature file has a matching
     @Given/@When/@Then method in the glue directory.
  2. Every matched method has a non-empty body (more than just whitespace, a
     single ';', or a trivial no-op like 'return;').

Usage:
  python3 verify_step_definition_parity.py \\
    --feature-files-dir <src/test/resources/features/> \\
    --glue-dir <src/test/java/com/example/steps/>
"""

import argparse
import os
import re
import sys
import textwrap


_FEATURE_STEP = re.compile(r'^\s+(Given|When|Then|And|But)\s+(.+)', re.MULTILINE)
_METHOD_ANNOTATION = re.compile(
    r'@(Given|When|Then|And|But)\s*\(\s*"([^"]*)"\s*\)')
_METHOD_BODY_START = re.compile(
    r'\b(public|protected|private)\s+\w+\s+(\w+)\s*\([^)]*\)'
    r'\s*(?:throws\s+\S+\s*)?\{')


def find_java_files(root):
    """Return all .java file paths under root, recursively."""
    result = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for f in filenames:
            if f.endswith(".java"):
                result.append(os.path.join(dirpath, f))
    return result


def extract_feature_steps(feature_path):
    """Return list of (step_type, step_text) tuples from a .feature file."""
    with open(feature_path, encoding='utf-8') as fh:
        text = fh.read()
    return _FEATURE_STEP.findall(text)


def extract_step_methods(java_sources):
    """Return { (annotation_type, step_text): body_text } for every step def.

    The key is (type, text) e.g. ('Given', 'the system is running').
    The value is the body text between { and }.
    """
    methods = {}
    for jpath in java_sources:
        with open(jpath, encoding='utf-8') as fh:
            text = fh.read()
        pos = 0
        while True:
            m = _METHOD_ANNOTATION.search(text, pos)
            if not m:
                break
            ann_type = m.group(1)
            step_text = m.group(2)
            # Find the next method body after this annotation
            body_start = text.find('{', m.end())
            if body_start < 0:
                pos = m.end()
                continue
            # Find matching closing brace (naive — good enough for step defs)
            depth = 0
            body_end = body_start
            for i in range(body_start, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        body_end = i
                        break
            body = text[body_start + 1:body_end].strip()
            methods[(ann_type, step_text)] = body
            pos = body_end + 1
    return methods


def is_trivial_body(body):
    """Return True if the method body is effectively empty."""
    # Remove single-line comments
    cleaned = re.sub(r'//.*', '', body)
    cleaned = cleaned.strip().rstrip(';')
    if not cleaned:
        return True
    # Single return statement with no value
    if cleaned == 'return':
        return True
    return False


def normalize_step(text):
    """Normalize Gherkin step text for comparison."""
    return text.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Verify every Gherkin step has a non-stub step definition")
    parser.add_argument("--feature-files-dir", required=True,
                        help="Cucumber feature file discovery directory")
    parser.add_argument("--glue-dir", required=True,
                        help="Step definition Java source directory")
    args = parser.parse_args()

    passed = True
    warn_count = 0

    if not os.path.isdir(args.feature_files_dir):
        print(f"FAIL  feature files directory not found: "
              f"{args.feature_files_dir}")
        sys.exit(1)

    if not os.path.isdir(args.glue_dir):
        print(f"FAIL  glue directory not found: {args.glue_dir}")
        sys.exit(1)

    # Collect all steps from all .feature files
    all_steps = []  # (filename, type, text)
    feature_files = [os.path.join(args.feature_files_dir, f)
                     for f in os.listdir(args.feature_files_dir)
                     if f.endswith(".feature")]
    if not feature_files:
        print(f"FAIL  no .feature files in {args.feature_files_dir}")
        sys.exit(1)

    for fp in feature_files:
        for step_type, step_text in extract_feature_steps(fp):
            all_steps.append((os.path.basename(fp), step_type, step_text))

    # Collect all step definitions from Java sources
    java_files = find_java_files(args.glue_dir)
    step_methods = extract_step_methods(java_files)

    # Check parity
    undefined = 0
    stub = 0
    for fname, step_type, step_text in all_steps:
        step_text = normalize_step(step_text)
        key = (step_type, step_text)
        if key not in step_methods:
            print(f"FAIL  {fname}: no @{step_type} definition for \"{step_text}\"")
            undefined += 1
            passed = False
        elif is_trivial_body(step_methods[key]):
            print(f"FAIL  {fname}: @{step_type}(\"{step_text}\") has an empty "
                  f"stub body — implement the step definition "
                  f"(method must contain actual test logic)")
            stub += 1
            passed = False

    # Also warn about unused step definitions
    used_keys = {(step_type, normalize_step(text)) for _, step_type, text in all_steps}
    unused = 0
    for key in step_methods:
        if key not in used_keys:
            unused += 1
    if unused > 0:
        print(f"WARN  {unused} step definition(s) have no matching "
              f"feature-file step — consider removing unused stubs")

    if passed:
        print(f"PASS  step definition parity: {len(all_steps)} steps covered, "
              f"0 undefined, 0 stubs")
        if unused:
            print(f"WARN  {unused} unused step definition(s) present "
                  f"(non-blocking)")
        sys.exit(0)
    else:
        print()
        print(textwrap.dedent(f"""\
            Agent instruction:
              {undefined} step(s) have no matching @Given/@When/@Then method.
              {stub} method(s) have empty stub bodies.
              Write the missing step definitions with actual implementations.
              Use the templates/step-definitions.java template as a starting point.
              Refer to methodology/architecture/GHERKIN_INTEGRATION.md for
              derivation rules.
        """))
        sys.exit(1)


if __name__ == "__main__":
    main()
