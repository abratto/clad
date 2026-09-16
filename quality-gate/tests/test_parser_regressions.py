#!/usr/bin/env python3
"""Regression fixtures for generic quality-gate parsing behavior."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))
import artifact_parsers as ap  # noqa: E402
IMPLEMENTATION_PARITY = REPO_ROOT / "quality-gate" / "verify_implementation_parity.py"
SYNC_PARITY = REPO_ROOT / "quality-gate" / "verify_sync_implementation_parity.py"
CUCUMBER_GREEN = REPO_ROOT / "quality-gate" / "verify_cucumber_green.py"


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run(script, *arguments):
    return subprocess.run(
        [sys.executable, str(script), *map(str, arguments)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def sync_rule(name, tconcept="Web", taction="request", toutcome="Routed",
              then_concept="Inventory", then_action="lend"):
    return (
        "class SyncRules {\n"
        f"    static SyncRule {name}() {{\n"
        "        return SyncRule.of(\n"
        f'            "{name}", "{tconcept}", "{taction}", "{toutcome}",\n'
        "            List.of(),\n"
        f'            List.of(invoke("{then_concept}", "{then_action}", Map.of())));\n'
        "    }\n"
        "}\n")


def canonical_sync(name, tconcept="Web", taction="request", toutcome="Routed",
                   then_concept="Inventory", then_action="lend"):
    return (
        f"sync {name}\n\n## Rule\n\nwhen {{\n"
        f"    {tconcept}/{taction}: [ x: ?x ] => [ {toutcome} ]\n"
        f"}}\nthen {{\n    {then_concept}/{then_action}: [ x: ?x ]\n}}\n")


class ImplementationParityFixtures(unittest.TestCase):

    def test_rule_contracts_lower_to_matching_sync_rules(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features = root / "features"
            syncs = root / "syncs"
            # Grammar v2 (effect-first, maintenance/sync-dsl-legibility.md).
            name = "InventoryLendForWidgetWhenWebRequestRouted"
            write(features / "UC-01-widget/stages/03_syncs/output" / f"{name}.sync.md",
                  canonical_sync(name))
            write(syncs / f"{name}.java", sync_rule(name))

            result = run(IMPLEMENTATION_PARITY, "--sync-impl-dir", syncs,
                         "--features-dir", features)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_sync_rule_without_spec_still_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            syncs = root / "syncs"
            write(syncs / "WhenMissingGoOkThenWebRespond.java",
                  sync_rule("WhenMissingGoOkThenWebRespond", "Go", "go", "Ok",
                            "Web", "respond"))

            result = run(IMPLEMENTATION_PARITY, "--sync-impl-dir", syncs,
                         "--features-dir", root / "features")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("No *.sync.md", result.stdout)

    def test_concept_implementation_without_spec_still_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            concepts = root / "concepts"
            write(concepts / "MissingConcept.java",
                  "public class MissingConcept implements Concept {}\n")

            result = run(IMPLEMENTATION_PARITY, "--concept-impl-dir", concepts,
                         "--features-dir", root / "features")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("MissingConcept", result.stdout)


class SyncImplementationParityFixtures(unittest.TestCase):

    def test_rule_spec_matches_sync_rule(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sync_dir = root / "syncs"
            impl_dir = root / "implementation"
            name = "InventoryLendWhenWebRequestRouted"
            write(sync_dir / f"{name}.sync.md", canonical_sync(name))
            write(impl_dir / f"{name}.java", sync_rule(name))

            result = run(SYNC_PARITY, "--sync-dir", sync_dir,
                         "--sync-impl-dir", impl_dir)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class CucumberGreenFixtures(unittest.TestCase):

    def run_report(self, suite_body):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        feature = root / "features/UC-01-widget"
        report = root / "target/surefire-reports/TEST-Cucumber.xml"
        feature.mkdir(parents=True)
        write(root / "clad.properties", "test.command=true\n")
        write(report, suite_body)
        return run(
            CUCUMBER_GREEN,
            "--feature-root", feature,
            "--test-command", "true",
            "--surefire-dir", report.parent,
        )

    def test_cucumber_test_suite_counts_passing_scenarios(self):
        result = self.run_report("""<testsuite name="example.steps.CucumberTest" tests="2" errors="0" skipped="0" failures="0">
  <testcase name="first scenario" classname="Widget Injector" />
  <testcase name="second scenario" classname="Widget Injector" />
</testsuite>""")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("2 Cucumber scenarios", result.stdout)

    def test_cucumber_test_suite_rejects_failing_skipped_and_zero_scenarios(self):
        failing = self.run_report("""<testsuite name="example.steps.CucumberTest" tests="1" errors="0" skipped="0" failures="1">
  <testcase name="broken scenario" classname="Widget Injector"><failure message="broken" /></testcase>
</testsuite>""")
        skipped = self.run_report("""<testsuite name="example.steps.CucumberTest" tests="1" errors="0" skipped="1" failures="0">
  <testcase name="pending scenario" classname="Widget Injector"><skipped /></testcase>
</testsuite>""")
        zero = self.run_report("""<testsuite name="example.steps.CucumberTest" tests="0" errors="0" skipped="0" failures="0" />""")

        self.assertNotEqual(failing.returncode, 0)
        self.assertNotEqual(skipped.returncode, 0)
        self.assertNotEqual(zero.returncode, 0)


class GoalScopeParsingTests(unittest.TestCase):
    """`parse_goals` must not count the `## Out of scope` table.

    The out-of-scope table repeats the `| Actor | Goal |` header but has no
    `In scope?` column; it was being read as in-scope (the conduit rebuild
    reported "19 in-scope goals" instead of 13)."""

    def test_out_of_scope_table_is_not_counted(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "goals.md"
            write(path,
                  "# Goals\n\n"
                  "| Actor | Goal | Rationale | Priority | In scope? |\n"
                  "|---|---|---|---|---|\n"
                  "| Member | Sign In | to authenticate | P0 | yes |\n"
                  "| Reader | List Tags | to see tags | P1 | yes |\n\n"
                  "## Out of scope\n\n"
                  "| Actor | Goal | Rationale |\n"
                  "|---|---|---|\n"
                  "| Member | Logout | not in the spec |\n"
                  "| System | Notify | no notification surface |\n")
            self.assertEqual(ap.parse_goals(str(path)), {"Sign In", "List Tags"})


if __name__ == "__main__":
    unittest.main()