#!/usr/bin/env python3
"""Regression coverage for the checker-scoping fixes.

These guard behaviors that were changed but only exercised via the end-to-end
runs: Cucumber-green module scoping / skip, concept-field assertions in flat
layouts, legacy route-filter blocking, step-definition skip when there is no
Cucumber glue, and the close-evidence warnings.
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


class CucumberGreenScopingTests(unittest.TestCase):
    def test_no_cucumber_reports_skips(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            feature = root / "features/UC-01-x"
            feature.mkdir(parents=True)
            write(root / "clad.properties", "test.command=true\n")
            result = run(str(QG / "verify_cucumber_green.py"),
                         "--feature-root", str(feature))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SKIP", result.stdout)

    def test_stale_report_in_another_module_is_ignored(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            feature = root / "features/UC-01-x"
            feature.mkdir(parents=True)
            write(root / "clad.properties",
                  "test.command=true -pl java-legible\n")
            write(root / "reference-impl/java-micronaut-jena/target/"
                  "surefire-reports/TEST-CucumberTest.xml",
                  '<testsuite name="CucumberTest" tests="2" failures="0" '
                  'errors="0" skipped="0">'
                  '<testcase name="a"/><testcase name="b"/></testsuite>')
            write(root / "reference-impl/java-legible/target/"
                  "surefire-reports/TEST-Foo.xml",
                  '<testsuite name="Foo" tests="1" failures="0" errors="0" '
                  'skipped="0"><testcase name="c"/></testsuite>')
            result = run(str(QG / "verify_cucumber_green.py"),
                         "--feature-root", str(feature))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SKIP", result.stdout)
            # The stale jena report (2 scenarios) must not be reported as this
            # profile's Cucumber evidence.
            self.assertNotIn("2 Cucumber scenarios", result.stdout)


class ConceptFieldAssertionFlatTests(unittest.TestCase):
    def _fixture(self, root, body):
        spec = root / "spec"
        tests = root / "tests/dev/legible/example/widget"
        write(spec / "Widget.spec.md",
              "# Widget\n\n### `check(userId)`\n"
              "- **Flow token:** `Widget.check { outcome, widgetId }`\n")
        write(tests / "WidgetCheckTest.java",
              "package dev.legible.example.widget;\n"
              "class WidgetCheckTest {\n"
              f"  @Test void shouldReturnWidget() {{ {body} }}\n"
              "}\n")
        return spec, tests

    def test_flat_concept_test_missing_field_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            spec, tests = self._fixture(
                Path(temporary),
                'var r = c.check(u); assertEquals("OK", r.readOutcome());')
            result = run(str(QG / "verify_concept_field_assertions.py"),
                         "--spec-dir", str(spec),
                         "--test-source-root", str(tests))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("widgetId", result.stdout)

    def test_flat_concept_test_with_field_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            spec, tests = self._fixture(
                Path(temporary),
                'var r = c.check(u); assertEquals("OK", r.readOutcome()); '
                'assertEquals("w1", r.get("widgetId"));')
            result = run(str(QG / "verify_concept_field_assertions.py"),
                         "--spec-dir", str(spec),
                         "--test-source-root", str(tests))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class LegacyRouteFilterTests(unittest.TestCase):
    def test_shared_trigger_without_route_guard_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            impl = Path(temporary)
            write(impl / "LoginRespond.java",
                  "class LoginRespond extends SyncAgent {\n"
                  "  SyncTrigger trigger() {\n"
                  "    return new SyncTrigger(SessionConcept.IRI, \"grant\");\n"
                  "  }\n"
                  "  String fires = \"Web/respond\";\n"
                  "  String whereClause() {\n"
                  "    return \"?u userId ?uid\";\n"
                  "  }\n"
                  "  String thenBindings() {\n"
                  "    return \"concept <http://x/concept/web>\";\n"
                  "  }\n"
                  "}\n")
            result = run(str(QG / "verify_sync_route_filters.py"),
                         "--sync-impl-dir", str(impl))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("route filter", result.stdout)


class StepDefinitionSkipTests(unittest.TestCase):
    def test_missing_glue_dir_skips(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root / "features/x.feature", "Feature: x\n")
            result = run(str(QG / "verify_step_definition_parity.py"),
                         "--feature-files-dir", str(root / "features"),
                         "--glue-dir", str(root / "does-not-exist"))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SKIP", result.stdout)


class CloseEvidenceTests(unittest.TestCase):
    def test_disabled_adapter_test_warns(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "UC-99-x"
            write(root / "stages/05_verify/output/trace.md", "Resume point: x\n")
            write(root / "stages/01b_chain-table/output/s-chain.md",
                  "| `Web/request[Routed]` | `Web.request` | `x` | `Routed` | e |\n")
            tests = Path(temporary) / "tests"
            write(tests / "WidgetFlowTest.java",
                  "class WidgetFlowTest { @Disabled @Test void f() {} }\n")
            result = run(str(QG / "verify_close_evidence.py"),
                         "--feature-root", str(root),
                         "--test-source-root", str(tests))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("WARN", result.stdout)
            self.assertIn("@Disabled", result.stdout)


class RehearsalRegressionTests(unittest.TestCase):
    def test_concept_matrix_does_not_cross_scenarios(self):
        sys.path.insert(0, str(QG))
        import verify_concept_matrix as vcm
        with tempfile.TemporaryDirectory() as temporary:
            chain = Path(temporary)
            (chain / "alpha-chain.md").write_text(
                "| 2 | `Alpha.do[Ok]` | `Web.respond[200]` | `x` | `Sent` | e |\n",
                encoding="utf-8")
            (chain / "beta-chain.md").write_text(
                "| 2 | `Beta.do[Ok]` | `Web.respond[200]` | `x` | `Sent` | e |\n",
                encoding="utf-8")
            matrix, _coverage = vcm.build_matrix(
                ["alpha", "beta"], ["Alpha", "Beta"], str(chain))
            self.assertEqual(matrix["alpha"], {"Alpha": "X"}, matrix)
            self.assertEqual(matrix["beta"], {"Beta": "X"}, matrix)

    def test_relational_mapping_ignores_prose_and_mutable(self):
        with tempfile.TemporaryDirectory() as temporary:
            d = Path(temporary)
            (d / "Inventory.storage.md").write_text(
                "# Inventory storage\n\n"
                "Fields are held in-place (mutable) in the concept region.\n"
                "The concept never references into another concept's region.\n",
                encoding="utf-8")
            result = run(str(QG / "verify_relational_mapping.py"),
                         "--storage-dir", str(d))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("no relational storage mappings", result.stdout)

    def test_action_log_isolation_warns_when_nothing_inspected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "WidgetApp.java").write_text(
                "class WidgetApp { FactStore factStore; }\n", encoding="utf-8")
            result = run(str(QG / "verify_action_log_isolation.py"),
                         "--app-source-root", str(root))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("WARN", result.stdout)
            self.assertIn("not evaluated", result.stdout)


if __name__ == "__main__":
    unittest.main()
