#!/usr/bin/env python3
"""
verify_concept_field_assertions.py - Enforce R14/R16 for Java concept tests.

For each Java concept test class that corresponds to a SPEC action, each
@Test method that asserts an outcome must also assert every required field
from that action's flow-token shape. Optional fields marked with '?' in the
SPEC are not required for every outcome.

Usage:
  python3 verify_concept_field_assertions.py \
    --spec-dir <04b_spec/output/> \
    --test-source-root <APP_TEST_SOURCE_ROOT>
"""

import argparse
import os
import re
import sys


ACTION_RE = re.compile(r"^###\s+`(\w+)\(")
FLOW_RE = re.compile(r"^- \*\*Flow token:\*\*\s+`?(\w+)\.(\w+)\s+\{([^}]*)\}`?")
PACKAGE_RE = re.compile(r"package\s+([\w.]+);")
CLASS_RE = re.compile(r"class\s+(\w+Test)\b")
TEST_RE = re.compile(r"@Test\b")
METHOD_RE = re.compile(r"\bvoid\s+(\w+)\s*\([^)]*\)\s*\{")


def pascal(name):
    return "".join(part[:1].upper() + part[1:] for part in re.split(r"[_\-]", name))


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def parse_required_fields(spec_dir):
    result = {}
    for fname in sorted(os.listdir(spec_dir)) if os.path.isdir(spec_dir) else []:
        if not fname.endswith(".spec.md"):
            continue
        concept = fname[:-len(".spec.md")]
        text = read(os.path.join(spec_dir, fname))
        current_action = None
        for line in text.splitlines():
            action_match = ACTION_RE.match(line.strip())
            if action_match:
                current_action = action_match.group(1)
                continue
            flow_match = FLOW_RE.match(line.strip())
            if flow_match:
                flow_concept, flow_action, fields_text = flow_match.groups()
                action = current_action or flow_action
                fields = []
                for raw_field in fields_text.split(","):
                    field = raw_field.strip().strip("`")
                    if not field or field == "outcome" or field.endswith("?"):
                        continue
                    fields.append(field)
                result[(flow_concept or concept, action)] = set(fields)
    return result


def matching_action(class_name, concept, actions):
    if not class_name.startswith(concept) or not class_name.endswith("Test"):
        return None
    middle = class_name[len(concept):-len("Test")]
    for action in actions:
        if middle == pascal(action):
            return action
    return None


def brace_body(text, open_brace_index):
    depth = 0
    for index in range(open_brace_index, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace_index + 1:index]
    return text[open_brace_index + 1:]


def test_methods(text):
    methods = []
    for test_match in TEST_RE.finditer(text):
        method_match = METHOD_RE.search(text, test_match.end())
        if not method_match:
            continue
        name = method_match.group(1)
        open_brace = text.find("{", method_match.end() - 1)
        if open_brace == -1:
            continue
        methods.append((name, brace_body(text, open_brace)))
    return methods


def has_outcome_assertion(body):
    return bool(re.search(r"assert\w*\s*\([^;]*(?:readOutcome\s*\(|\boutcome\b)", body))


def is_refusal_test(body):
    """A test that asserts 'refused' outcome or 'refusalReason' tests a
    refused action — no happy-path flow-token fields are expected."""
    has_refused_outcome = bool(re.search(r'"refused"', body))
    has_refusal_reason = bool(re.search(r'refusalReason', body))
    return has_refused_outcome or has_refusal_reason


def has_field_assertion(body, field):
    field_ref = re.escape(field)
    patterns = [
        rf"assert\w*\s*\([^;]*readField\s*\(\s*\"{field_ref}\"\s*\)",
        rf"assert\w*\s*\([^;]*binding\s*\(\s*\"{field_ref}\"\s*\)",
        rf"assert\w*\s*\([^;]*\.get\s*\(\s*\"{field_ref}\"\s*\)",
    ]
    return any(re.search(pattern, body, re.DOTALL) for pattern in patterns)


def scan_tests(test_source_root, required_by_action):
    failures = []
    checked = 0
    actions_by_concept = {}
    for concept, action in required_by_action:
        actions_by_concept.setdefault(concept, set()).add(action)

    for root, dirs, files in os.walk(test_source_root):
        if ".git" in root:
            continue
        for fname in files:
            if not fname.endswith("Test.java"):
                continue
            path = os.path.join(root, fname)
            text = read(path)
            package_match = PACKAGE_RE.search(text)
            if not package_match or ".concepts." not in package_match.group(1):
                continue
            class_match = CLASS_RE.search(text)
            if not class_match:
                continue
            class_name = class_match.group(1)
            concept_slug = package_match.group(1).split(".concepts.", 1)[1].split(".", 1)[0]
            concept_name = next(
                (name for name in actions_by_concept if name.lower() == concept_slug.lower()),
                pascal(concept_slug),
            )
            action = matching_action(class_name, concept_name, actions_by_concept.get(concept_name, set()))
            if not action:
                continue
            required_fields = required_by_action.get((concept_name, action), set())
            if not required_fields:
                continue
            for method_name, body in test_methods(text):
                if not has_outcome_assertion(body):
                    continue
                if is_refusal_test(body):
                    continue
                checked += 1
                for field in sorted(required_fields):
                    if not has_field_assertion(body, field):
                        failures.append(
                            f"{path}: {class_name}.{method_name}() asserts outcome "
                            f"but not required completion field '{field}'"
                        )
    return checked, failures


def main():
    parser = argparse.ArgumentParser(
        description="Verify Java concept tests assert required completion fields"
    )
    parser.add_argument("--spec-dir", required=True)
    parser.add_argument("--test-source-root", required=True)
    args = parser.parse_args()

    if not os.path.isdir(args.spec_dir):
        print(f"FAIL  SPEC directory not found: {args.spec_dir}")
        return 1
    if not os.path.isdir(args.test_source_root):
        print(f"FAIL  test source root not found: {args.test_source_root}")
        return 1

    required_by_action = parse_required_fields(args.spec_dir)
    if not required_by_action:
        print("WARN  no required flow-token fields parsed from SPECs")
        return 0

    checked, failures = scan_tests(args.test_source_root, required_by_action)
    if failures:
        print(f"FAIL  R14/R16 field assertion check failed ({len(failures)} issue(s))")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"PASS  R14/R16: {checked} concept test method(s) assert required fields")
    return 0


if __name__ == "__main__":
    sys.exit(main())