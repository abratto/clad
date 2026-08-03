#!/usr/bin/env python3
"""Regression fixtures for generic quality-gate parsing behavior."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
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


def sync_class(name):
    return f'''@Singleton
public class {name} extends SyncAgent {{
    public String syncName() {{ return "{name[:1].lower()}{name[1:]}"; }}
}}
'''


class ImplementationParityFixtures(unittest.TestCase):

    def test_compact_matrix_contracts_lower_to_matching_sync_classes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features = root / "features"
            syncs = root / "syncs"
            contracts = [
                ("UC-01-widget-injector", "Whitelist", "add"),
                ("UC-01-widget-injector", "Whitelist", "check"),
                ("UC-02-intent-query", "LegalOntology", "queryService"),
                ("UC-02-intent-query", "LegalOntology", "listServices"),
            ]
            compact_signatures = [
                "Routed(domain)",
                "Routed(clientId, origin)",
                "Routed(clientId, text)",
                "Routed(clientId, text)",
            ]

            for (feature, target, action), completion in zip(contracts, compact_signatures):
                scope = "WidgetInjector" if "widget" in feature else "IntentQuery"
                name = f"WhenWebHandleRoutedThen{target}{action[:1].upper()}{action[1:]}For{scope}"
                write(
                    features / feature / "stages/03_syncs/output" / f"{name}.sync.md",
                    f"""sync {name}

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature |
|---|---|---|---|
| 1 | 2 | `Web/handle: [{completion}]` | `{target}/{action}: [ value: String ]` |
""",
                )
                write(syncs / f"{name}.java", sync_class(name))

            result = run(
                IMPLEMENTATION_PARITY,
                "--sync-impl-dir", syncs,
                "--features-dir", features,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_malformed_compact_matrix_signature_still_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features = root / "features"
            syncs = root / "syncs"
            name = "WhenWebHandleRoutedThenWhitelistAddForWidget"
            write(
                features / "UC-01-widget/stages/03_syncs/output" / f"{name}.sync.md",
                f"""sync {name}

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature |
|---|---|---|---|
| 1 | 2 | `Web/handle [Routed(domain)]` | `Whitelist/add: [ domain: String ]` |
""",
            )
            write(syncs / f"{name}.java", sync_class(name))

            result = run(
                IMPLEMENTATION_PARITY,
                "--sync-impl-dir", syncs,
                "--features-dir", features,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("could not derive mechanical", result.stdout)

    def test_matrix_and_rule_contracts_lower_and_spi_is_not_a_concept(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features = root / "features"
            syncs = root / "syncs"
            concepts = root / "concepts"

            write(
                features / "UC-01-widget" / "stages/03_syncs/output/"
                "WhenWidgetSessionStartCreatedThenWebRespondForWidget.sync.md",
                """sync WhenWidgetSessionStartCreatedThenWebRespondForWidget

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| 3 | 4 | `WidgetSession/start: [ clientId: String ] => [ CREATED(sessionId) ]` | `Web/respond: [ status: 200 ; body: { sessionId } ]` | 200 |
""",
            )
            write(
                features / "UC-02-rule" / "stages/03_syncs/output/"
                "WhenWidgetSessionStartCreatedThenWebRespondForRule.sync.md",
                """sync WhenWidgetSessionStartCreatedThenWebRespondForRule

## Rule

when  WidgetSession/start [ CREATED(sessionId) ]
then {
    Web/respond: [ status: 200 ; body: { sessionId: $_sessionId } ]
}
""",
            )
            write(syncs / "WhenWidgetSessionStartCreatedThenWebRespondForWidget.java",
                  sync_class("WhenWidgetSessionStartCreatedThenWebRespondForWidget"))
            write(syncs / "WhenWidgetSessionStartCreatedThenWebRespondForRule.java",
                  sync_class("WhenWidgetSessionStartCreatedThenWebRespondForRule"))
            write(features / "UC-01-widget/stages/02_concepts/output/Widget.concept.md", "# Widget\n")
            write(concepts / "WidgetConcept.java", "public class WidgetConcept extends ConceptAgent {}\n")
            write(concepts / "widget/spi/LegalDomainExtractor.java",
                  "public interface LegalDomainExtractor {}\n")

            result = run(
                IMPLEMENTATION_PARITY,
                "--sync-impl-dir", syncs,
                "--concept-impl-dir", concepts,
                "--features-dir", features,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_real_concept_agent_without_spec_still_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            concepts = root / "concepts"
            features = root / "features"
            write(concepts / "MissingConcept.java", "public class MissingConcept extends ConceptAgent {}\n")

            result = run(
                IMPLEMENTATION_PARITY,
                "--concept-impl-dir", concepts,
                "--features-dir", features,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("MissingConcept", result.stdout)

    def test_missing_sync_spec_still_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            syncs = root / "syncs"
            write(syncs / "WhenMissingGoOkThenWebRespond.java",
                  sync_class("WhenMissingGoOkThenWebRespond"))

            result = run(
                IMPLEMENTATION_PARITY,
                "--sync-impl-dir", syncs,
                "--features-dir", root / "features",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("No *.sync.md", result.stdout)


class SyncImplementationParityFixtures(unittest.TestCase):

    def test_compact_matrix_completion_notation_is_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sync_dir = root / "syncs"
            impl_dir = root / "implementation"
            name = "WhenWebHandleRoutedThenWebRespond"
            write(
                sync_dir / f"{name}.sync.md",
                f"""sync {name}

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature |
|---|---|---|---|
| 1 | 2 | `Web/handle: [Routed(clientId, origin)]` | `Web/respond: [ status: 200 ]` |
""",
            )
            write(impl_dir / f"{name}.java", sync_class(name))

            result = run(SYNC_PARITY, "--sync-dir", sync_dir, "--sync-impl-dir", impl_dir)

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


if __name__ == "__main__":
    unittest.main()