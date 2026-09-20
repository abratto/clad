#!/usr/bin/env python3
"""
verify_concept_field_assertions.py - Enforce R14/R16 for Java concept tests.

For each Java concept test class that corresponds to a contract action, each
@Test method that asserts an outcome must also assert every required field
from that action's flow-token shape. Optional fields marked with '?' in the
contract are not required for every outcome.

Usage:
  python3 verify_concept_field_assertions.py \
    --contract-dir <04b_contract/output/> \
    --test-source-root <APP_TEST_SOURCE_ROOT>
"""

import argparse

from artifact_parsers import merge_by_concept  # noqa: E402
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


def parse_required_fields(contract_dir):
    result = {}
    for fname in sorted(os.listdir(contract_dir)) if os.path.isdir(contract_dir) else []:
        if not fname.endswith(".contract.md"):
            continue
        concept = fname[:-len(".contract.md")]
        text = read(os.path.join(contract_dir, fname))
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
                # One action may declare several flow-token shapes (modes),
                # e.g. an overloaded read keyed by userId vs username, or an
                # action that completes differently per outcome. Keep one
                # required-field set per declared mode so a test that exercises
                # one mode is not forced to assert another mode's fields.
                result.setdefault((flow_concept or concept, action), []).append(set(fields))
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
            class_match = CLASS_RE.search(text)
            if not class_match:
                continue
            class_name = class_match.group(1)
            # Locate the concept this test belongs to. Prefer the legacy/canonical
            # `.concepts.<slug>` package bucket; also accept the flat profile
            # layout used by the reference impls (`...example.<concept>.<Concept><Action>Test`),
            # matched by class-name prefix so flow/sync tests are not misread.
            concept_name = None
            package_match = PACKAGE_RE.search(text)
            if package_match and ".concepts." in package_match.group(1):
                concept_slug = package_match.group(1).split(".concepts.", 1)[1].split(".", 1)[0]
                concept_name = next(
                    (name for name in actions_by_concept
                     if name.lower() == concept_slug.lower()),
                    pascal(concept_slug),
                )
            if concept_name is None:
                for name in sorted(actions_by_concept, key=len, reverse=True):
                    if class_name.lower().startswith(name.lower()):
                        concept_name = name
                        break
            if concept_name is None:
                continue
            action = matching_action(class_name, concept_name, actions_by_concept.get(concept_name, set()))
            if not action:
                continue
            required_modes = required_by_action.get((concept_name, action), [])
            # Modes that require nothing impose no assertion; a method only
            # needs to satisfy the required fields of the one mode it exercises.
            required_modes = [fields for fields in required_modes if fields]
            if not required_modes:
                continue
            for method_name, body in test_methods(text):
                if not has_outcome_assertion(body):
                    continue
                if is_refusal_test(body):
                    continue
                checked += 1
                best_missing = None
                for fields in required_modes:
                    missing = sorted(f for f in fields if not has_field_assertion(body, f))
                    if not missing:
                        best_missing = None
                        break
                    if best_missing is None or len(missing) < len(best_missing):
                        best_missing = missing
                if best_missing:
                    for field in best_missing:
                        failures.append(
                            f"{path}: {class_name}.{method_name}() asserts outcome "
                            f"but not required completion field '{field}'"
                        )
    return checked, failures


def main():
    parser = argparse.ArgumentParser(
        description="Verify Java concept tests assert required completion fields"
    )
    parser.add_argument(
        "--contract-dir", required=True, action="append",
        help="Contract dir; repeatable. Earlier dirs shadow later, so a reused "
             "concept's tests are checked against its canonical contract (R22)")
    parser.add_argument("--test-source-root", required=True)
    args = parser.parse_args()

    if not os.path.isdir(args.test_source_root):
        print(f"FAIL  test source root not found: {args.test_source_root}")
        return 1

    required_by_action = merge_by_concept(args.contract_dir, parse_required_fields)
    if not required_by_action:
        print("WARN  no required flow-token fields parsed from contracts")
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