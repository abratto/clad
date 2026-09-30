#!/usr/bin/env python3
"""
verify_acceptance_binding.py — Stage gate: Acceptance Spec ↔ native tests.

Why this exists (DR-0001):
  The Gherkin/Cucumber outer track was replaced by native per-scenario flow
  tests plus a generated, frozen Acceptance Spec
  (`04c_acceptance-tests/output/acceptance-spec.md`). The Spec is the
  human-facing Gate-3 artifact; this checker guarantees it is a truthful index
  of the executable suite by enforcing a 1:1 binding:

    1. Every top-level scenario in `usecase.md` has a `## Scenario:` section
       in the Acceptance Spec.
    2. Every section names a `Test:` method (`Class.method`), and that method
       exists in the configured test source root.
    3. Every `@Test` method of a `*FlowTest.java` in the test source root is
       referenced by the Spec (no undocumented flow test).

  (2) and (3) together are what lets a reviewer trust that the Spec is the test
  suite. The freeze itself is provided by the Gate-3 content hash: editing the
  Spec after approval stales the gate and forces re-approval.

Acceptance Spec grammar (see `templates/acceptance-spec.md`):
  `## Scenario: <name>` matching the use-case scenario name exactly, and one
  or more `- **Test:** `Class.method`` bullets, each binding a scenario (or a
  sub-case) to the native test method that enforces it.

Usage:
  python3 verify_acceptance_binding.py --spec <acceptance-spec.md> \
    --usecase <usecase.md> --chain-dir <dir> --test-source-root <dir>
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys

SCENARIO_RE = re.compile(r"^###\s+Scenario:\s*(.+?)\s*$", re.MULTILINE)
SPEC_SECTION_RE = re.compile(r"^##\s+Scenario:\s*(.+?)\s*$", re.MULTILINE)
TEST_BIND_RE = re.compile(r"\*\*Test:\*\*\s*`([A-Za-z_][\w]*)\.([A-Za-z_][\w]*)`")
FLOW_TEST_METHOD_RE = re.compile(
    r"@Test\b[\s\S]*?\bvoid\s+([A-Za-z_]\w*)\s*\(")


def parse_usecase_scenarios(path: str) -> list[str]:
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8", errors="replace") as fh:
        return [m.strip() for m in SCENARIO_RE.findall(fh.read())]


def parse_acceptance_spec(path: str) -> tuple[list[str], list[tuple[str, str]]]:
    """Return (scenario names, [(class, method)])."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    names = [m.strip() for m in SPEC_SECTION_RE.findall(text)]
    binds = [(c, m) for c, m in TEST_BIND_RE.findall(text)]
    return names, binds


def _documented_union(spec_path: str, own_binds: list) -> set:
    """Every `Class.method` documented by an acceptance spec in this repo.

    The "no undocumented flow test" rule is a repo-level orphan check, not a
    per-spec one: in a shared test source root a flow test may legitimately
    belong to another feature. Comparing every flow test against *this* spec
    forced each feature to index every other feature's tests. When the spec is
    not inside a `features/` tree (a standalone fixture), fall back to this
    spec's own bindings.
    """
    documented = set()
    spec = os.path.abspath(spec_path)
    parent = os.path.dirname(spec)
    while parent and os.path.basename(parent) != "features":
        nxt = os.path.dirname(parent)
        if nxt == parent:
            parent = ""
            break
        parent = nxt
    if not parent or os.path.basename(parent) != "features":
        return set(own_binds)
    pattern = os.path.join(parent, "*", "stages", "04_implement",
                           "04c_acceptance-tests", "output", "acceptance-spec.md")
    for path in glob.glob(pattern):
        try:
            _names, binds = parse_acceptance_spec(path)
        except OSError:
            continue
        documented.update(binds)
    return documented or set(own_binds)


def _index_test_methods(root: str) -> dict[str, set[str]]:
    """Map class name -> set of method names for every .java under `root`."""
    index: dict[str, set[str]] = {}
    if not root or not os.path.isdir(root):
        return index
    class_re = re.compile(r"\bclass\s+([A-Za-z_]\w*)")
    method_re = re.compile(r"\bvoid\s+([A-Za-z_]\w*)\s*\(")
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if not name.endswith(".java"):
                continue
            with open(os.path.join(dirpath, name), encoding="utf-8",
                      errors="replace") as fh:
                text = fh.read()
            for cls in class_re.findall(text):
                index.setdefault(cls, set()).update(method_re.findall(text))
    return index


def _flow_test_methods(root: str) -> list[tuple[str, str]]:
    """(class, method) for every @Test method of a *FlowTest.java."""
    found: list[tuple[str, str]] = []
    if not root or not os.path.isdir(root):
        return found
    class_re = re.compile(r"\bclass\s+([A-Za-z_]\w*)")
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if not name.endswith("FlowTest.java"):
                continue
            with open(os.path.join(dirpath, name), encoding="utf-8",
                      errors="replace") as fh:
                text = fh.read()
            cls_match = class_re.search(text)
            if not cls_match:
                continue
            cls = cls_match.group(1)
            for method in FLOW_TEST_METHOD_RE.findall(text):
                found.append((cls, method))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify Acceptance Spec ↔ native flow-test binding")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--usecase", required=True)
    parser.add_argument("--chain-dir", default="")
    parser.add_argument("--test-source-root", default="")
    args = parser.parse_args()

    if not os.path.isfile(args.spec):
        print(f"FAIL  acceptance spec not found: {args.spec}")
        return 1

    scenario_names, binds = parse_acceptance_spec(args.spec)
    usecase_scenarios = parse_usecase_scenarios(args.usecase)
    ok = True

    if not scenario_names:
        print("FAIL  acceptance spec has no `## Scenario:` sections")
        return 1
    if not binds:
        print("FAIL  acceptance spec has no `- **Test:** `Class.method`` binding")
        return 1

    missing = [s for s in usecase_scenarios if s not in scenario_names]
    if missing:
        ok = False
        print(f"FAIL  {len(missing)} use-case scenario(s) absent from the "
              f"acceptance spec: {', '.join(missing)}")

    extra = [s for s in scenario_names if s not in usecase_scenarios]
    if extra:
        # An extra scenario the use case does not define is an invented
        # contract (the old Gherkin rule: a derived view invents nothing).
        ok = False
        print(f"FAIL  acceptance spec has scenario(s) not in usecase.md: "
              f"{', '.join(extra)}")

    index = _index_test_methods(args.test_source_root)
    if not args.test_source_root or not os.path.isdir(args.test_source_root):
        print("WARN  test source root absent — binding to methods skipped")
    else:
        for cls, method in binds:
            methods = index.get(cls)
            if methods is None:
                ok = False
                print(f"FAIL  bound test class not found: {cls} ({cls}.{method})")
            elif method not in methods:
                ok = False
                print(f"FAIL  bound test method not found: {cls}.{method}")

        documented = _documented_union(args.spec, binds)
        for cls, method in _flow_test_methods(args.test_source_root):
            if (cls, method) not in documented:
                ok = False
                print(f"FAIL  undocumented flow test: {cls}.{method} — add a "
                      f"`Test:` binding or remove the method")

    if ok:
        print(f"PASS  acceptance spec binds {len(scenario_names)} scenario(s) "
              f"and {len(binds)} test(s)")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
