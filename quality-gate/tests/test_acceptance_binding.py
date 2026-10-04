#!/usr/bin/env python3
"""Regression coverage for verify_acceptance_binding.py (DR-0001).

The Acceptance Spec is the frozen Gate-3 artifact; this checker proves it is a
truthful index of the native flow tests.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"


def run(*args):
    return subprocess.run([sys.executable, *args], cwd=REPO_ROOT,
                          capture_output=True, text=True)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


USECASE = (
    "# UC-01 — Widget\n\n## Scenarios\n\n"
    "### Scenario: create-widget\n\n- Trigger: submit.\n\n"
    "### Scenario: delete-widget\n\n- Trigger: delete.\n"
)

SPEC = (
    "# Acceptance spec\n\n"
    "## Scenario: create-widget\n\n- **Test:** `WidgetFlowTest.createWorks`\n\n"
    "## Scenario: delete-widget\n\n- **Test:** `WidgetFlowTest.deleteWorks`\n"
)

FLOW_TEST = (
    "package example;\n"
    "class WidgetFlowTest {\n"
    "  @Test void createWorks() {}\n"
    "  @Test void deleteWorks() {}\n"
    "}\n"
)


class AcceptanceBindingTests(unittest.TestCase):

    def fixture(self, temporary, *, usecase=USECASE, spec=SPEC, flow=FLOW_TEST):
        root = Path(temporary)
        usecase_path = root / "usecase.md"
        spec_path = root / "acceptance-spec.md"
        tests = root / "src/test/java/example"
        write(usecase_path, usecase)
        write(spec_path, spec)
        if flow is not None:
            write(tests / "WidgetFlowTest.java", flow)
        return spec_path, usecase_path, (tests if flow is not None else root / "missing")

    def invoke(self, fixture):
        spec_path, usecase_path, tests = fixture
        return run(str(QG / "verify_acceptance_binding.py"),
                   "--spec", str(spec_path),
                   "--usecase", str(usecase_path),
                   "--test-source-root", str(tests))

    def test_complete_binding_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            r = self.invoke(self.fixture(temporary))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_missing_scenario_fails(self):
        spec = SPEC.replace("## Scenario: delete-widget\n\n- **Test:** `WidgetFlowTest.deleteWorks`\n", "")
        with tempfile.TemporaryDirectory() as temporary:
            r = self.invoke(self.fixture(temporary, spec=spec))
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("delete-widget", r.stdout)

    def test_invented_scenario_fails(self):
        spec = SPEC + "\n## Scenario: invented\n\n- Test: `WidgetFlowTest.createWorks`\n"
        with tempfile.TemporaryDirectory() as temporary:
            r = self.invoke(self.fixture(temporary, spec=spec))
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("invented", r.stdout)

    def test_missing_test_method_fails(self):
        spec = SPEC.replace("WidgetFlowTest.deleteWorks", "WidgetFlowTest.doesNotExist")
        with tempfile.TemporaryDirectory() as temporary:
            r = self.invoke(self.fixture(temporary, spec=spec))
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("doesNotExist", r.stdout)

    def test_undocumented_flow_test_method_fails(self):
        flow = FLOW_TEST.replace("  @Test void createWorks() {}\n",
                                 "  @Test void createWorks() {}\n  @Test void undocumented() {}\n")
        with tempfile.TemporaryDirectory() as temporary:
            r = self.invoke(self.fixture(temporary, flow=flow))
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("undocumented", r.stdout)

    def test_no_test_root_warns_but_checks_scenarios(self):
        with tempfile.TemporaryDirectory() as temporary:
            r = self.invoke(self.fixture(temporary, flow=None))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("WARN", r.stdout)

    def test_no_binding_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            r = self.invoke(self.fixture(temporary, spec="# empty\n"))
            self.assertNotEqual(r.returncode, 0)

    def test_foreign_flow_test_documented_by_a_sibling_spec_is_not_required(self):
        """Rule (3) is a repo-level orphan check, not a per-spec one.

        A shared test source root holds several features' flow tests; this
        spec must not have to index another feature's tests for them to count
        as documented."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features = root / "features"
            this_spec = (features / "UC-02-x/stages/04_implement/"
                         "04c_acceptance-tests/output/acceptance-spec.md")
            this_usecase = features / "UC-02-x/stages/01_usecase/output/usecase.md"
            write(this_spec, SPEC)
            write(this_usecase, USECASE)
            write(features / "UC-01-y/stages/04_implement/04c_acceptance-tests/"
                  "output/acceptance-spec.md",
                  "# Acceptance spec\n\n## Scenario: other\n\n"
                  "- **Test:** `OtherFlowTest.otherWorks`\n")
            tests = root / "src/test/java/example"
            write(tests / "WidgetFlowTest.java", FLOW_TEST)
            write(tests / "OtherFlowTest.java",
                  "package example;\nclass OtherFlowTest {"
                  " @Test void otherWorks() {} }\n")
            r = run(str(QG / "verify_acceptance_binding.py"),
                    "--spec", str(this_spec), "--usecase", str(this_usecase),
                    "--test-source-root", str(tests))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_orphan_flow_test_with_no_spec_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features = root / "features"
            this_spec = (features / "UC-02-x/stages/04_implement/"
                         "04c_acceptance-tests/output/acceptance-spec.md")
            this_usecase = features / "UC-02-x/stages/01_usecase/output/usecase.md"
            write(this_spec, SPEC)
            write(this_usecase, USECASE)
            tests = root / "src/test/java/example"
            write(tests / "WidgetFlowTest.java", FLOW_TEST)
            write(tests / "OrphanFlowTest.java",
                  "package example;\nclass OrphanFlowTest {"
                  " @Test void orphan() {} }\n")
            r = run(str(QG / "verify_acceptance_binding.py"),
                    "--spec", str(this_spec), "--usecase", str(this_usecase),
                    "--test-source-root", str(tests))
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("Orphan", r.stdout)


if __name__ == "__main__":
    unittest.main()
