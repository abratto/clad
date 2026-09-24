#!/usr/bin/env python3
"""Regression coverage for the gap-closure checks (G1-G7, G10)."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
UC00_SYNCS = REPO_ROOT / "examples/UC-00-login/stages/03_syncs/output"
LOGIN_IMPL = REPO_ROOT / "reference-impl/java-legible/src/main/java/dev/legible/example/login"




def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def run(*args, cwd=REPO_ROOT):
    return subprocess.run([sys.executable, *args], cwd=cwd,
                          capture_output=True, text=True)


class SyncParityTests(unittest.TestCase):
    def test_strict_trigger_passes_canonical_login(self):
        result = run(str(QG / "verify_sync_implementation_parity.py"),
                     "--sync-dir", str(UC00_SYNCS),
                     "--sync-impl-dir", str(LOGIN_IMPL), "--strict-trigger")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_strict_trigger_catches_wrong_then_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            impl = Path(temporary)
            (impl / "S.java").write_text(
                'class S {\n'
                '  static SyncRule a() {\n'
                '    return SyncRule.of(\n'
                '        "RespondForLoginWhenGrantGranted",\n'
                '        "Session", "grant", "GRANTED",\n'
                '        List.of(),\n'
                '        List.of(invoke("Book", "reserve", Map.of())));\n'
                '  }\n'
                '}\n', encoding="utf-8")
            result = run(str(QG / "verify_sync_implementation_parity.py"),
                         "--sync-dir", str(UC00_SYNCS),
                         "--sync-impl-dir", str(impl), "--strict-trigger")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("then mismatch", result.stdout)


class FalseGreenTests(unittest.TestCase):
    """A gate must not exit 0 on a defect: missing input may skip, but present
    input that yields nothing comparable must FAIL
    (maintenance/gate-verdict-hardening.md)."""

    def _run(self, script, *args):
        return run(str(QG / script), *args)

    def test_outcome_alignment_fails_on_empty_chain_rows(self):
        # A chain file whose every row is a terminal respond row parses to zero
        # comparable rows: a defect, not an absence.
        with tempfile.TemporaryDirectory() as temporary:
            chain = Path(temporary) / "chain"
            chain.mkdir()
            write(chain / "login-chain.md",
                  "## Chain\n\n"
                  "| # | When | Then |\n|---|---|---|\n"
                  "| 1 | `Web/request: [ ... ] => [ Routed ]` | `Web/respond: [ 200 ]` |\n")
            contract = Path(temporary) / "contract"
            contract.mkdir()
            write(contract / "UserNaming.contract.md", "# UserNaming — contract\n")
            result = self._run("verify_outcome_alignment.py",
                               "--chain-dir", str(chain),
                               "--contract-dir", str(contract))
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("FAIL", result.stdout)

    def test_outcome_alignment_skips_when_chain_dir_absent(self):
        with tempfile.TemporaryDirectory() as temporary:
            contract = Path(temporary) / "contract"
            contract.mkdir()
            write(contract / "UserNaming.contract.md", "# UserNaming — contract\n")
            result = self._run("verify_outcome_alignment.py",
                               "--chain-dir", str(Path(temporary) / "missing"),
                               "--contract-dir", str(contract))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SKIP", result.stdout)

    def test_scenario_coverage_fails_on_missing_chain_dir_with_scenarios(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root / "goals.md",
                  "## In scope\n\n- Sign in\n")
            write(root / "usecase.md",
                  "## Scenarios\n\n### Scenario: sign-in\n\nstuff\n")
            result = self._run("verify_scenario_coverage.py",
                               "--goals", str(root / "goals.md"),
                               "--usecase", str(root / "usecase.md"),
                               "--chain-dir", str(root / "no-chain"),
                               "--sync-dir", str(root / "no-sync"))
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("FAIL", result.stdout)

    def test_additivity_fails_on_missing_proposal_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            feature = root / "features/UC-01-x"
            write(feature / "stages/01a_responsibility-map/output/responsibility-map.md",
                  "| Concept | Origin | Owned state | Owned actions | Notes |\n|---|---|---|---|---|\n"
                  "| `Widget` | `extends:UC-00` | `x: Map<Id, V>` | `act` | — |\n")
            corpus = root / "corpus"
            write(corpus / "Widget.concept.md", "# Widget\n\n## State\n\nx\n")
            # A canonical contract exists; the proposal's 04b_contract is empty.
            write(corpus / "Widget.contract.md",
                  "# Widget — contract\n\n## Actions\n\n"
                  "### `act(order: OrderId)`\n\n"
                  "- **Outcomes:** `OK`, `Refused`\n")
            (feature / "stages/04_implement/04b_contract/output").mkdir(parents=True)
            result = self._run("verify_concept_additivity.py",
                               "--feature", str(feature), "--corpus", str(corpus))
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("contract", result.stdout.lower())

    def test_shared_triggers_ignores_whitespace_eol_drift(self):
        # A generated view that differs only by trailing whitespace / CRLF is
        # current (logical comparison), not stale.
        with tempfile.TemporaryDirectory() as temporary:
            features = Path(temporary) / "features"
            system = features / "_system"
            system.mkdir(parents=True)
            import sys as _sys
            _sys.path.insert(0, str(QG))
            import generate_shared_triggers as gst
            fresh = gst.render(str(features))
            drifted = "\r\n".join(line + "   " for line in fresh.split("\n"))
            write(system / "shared-triggers.md", drifted)
            result = self._run("verify_shared_triggers_current.py",
                               "--features-dir", str(features))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS", result.stdout)



    def _root(self, temporary):
        root = Path(temporary) / "dev/legible/example/health"
        root.mkdir(parents=True)
        return root

    def test_flat_concept_test_is_selected_and_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            (root / "HealthCheckTest.java").write_text(
                "package dev.legible.example.health;\n"
                "class HealthCheckTest {\n"
                "  @Nested class WhenHealthy {\n"
                "    @Test void shouldReturnHealthy() { // GIVEN // WHEN // THEN\n"
                "      Object c = new HealthConcept(); } }\n}\n",
                encoding="utf-8")
            (root / "HealthFlowTest.java").write_text(
                "package dev.legible.example.health;\n"
                "class HealthFlowTest { @Test void flow() {} }\n",
                encoding="utf-8")
            result = run(str(QG / "verify_test_naming.py"),
                         "--test-source-root", str(root.parent.parent.parent),
                         "--scope", "concepts")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("HealthCheckTest", result.stdout)
            self.assertNotIn("HealthFlowTest", result.stdout)


class ActionLogIsolationTests(unittest.TestCase):
    def test_canonical_violation_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "Handler.java").write_text(
                "class Handler { void x(FactStore factStore) { "
                "factStore.region(\"User\"); } }\n", encoding="utf-8")
            (root / "WidgetConcept.java").write_text(
                "class WidgetConcept { FactStore factStore; }\n", encoding="utf-8")
            result = run(str(QG / "verify_action_log_isolation.py"),
                         "--app-source-root", str(root))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("FactStore", result.stdout)

    def test_unknown_layout_warns_and_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "Foo.java").write_text("class Foo {}\n", encoding="utf-8")
            result = run(str(QG / "verify_action_log_isolation.py"),
                         "--app-source-root", str(root))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("WARN", result.stdout)


class RouteFilterAmbiguityTests(unittest.TestCase):
    def test_duplicate_trigger_warns_but_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            impl = Path(temporary)
            (impl / "D.java").write_text(
                'class D {\n'
                '  static SyncRule a() { return SyncRule.of("A","Session","grant",'
                '"GRANTED",List.of(),List.of(invoke("Web","respond",Map.of()))); }\n'
                '  static SyncRule b() { return SyncRule.of("B","Session","grant",'
                '"GRANTED",List.of(),List.of(invoke("Web","respond",Map.of()))); }\n'
                '}\n', encoding="utf-8")
            result = run(str(QG / "verify_sync_route_filters.py"),
                         "--sync-impl-dir", str(impl))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("WARN", result.stdout)


class DescriptorCompletenessTests(unittest.TestCase):
    def test_expected_outputs_cover_all_stages(self):
        result = run(str(QG / "describe_feature.py"),
                     "--feature", str(REPO_ROOT / "examples/UC-00-login"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        expected = json.loads(result.stdout)["expectedOutputs"]
        for stage_id in ("01", "01a", "01b", "02", "03", "03a", "03b",
                         "04a", "04b", "04c", "04d-red", "04d-green",
                         "04e-red", "04e-green", "05"):
            self.assertIn(stage_id, expected)
        self.assertEqual(expected["04c"], ["login.feature"])


class CloseEvidenceTests(unittest.TestCase):
    def _feature(self, root, trace_name="verification-trace.md"):
        out = root / "stages/05_verify/output"
        out.mkdir(parents=True)
        (out / trace_name).write_text("Resume point: x\n", encoding="utf-8")
        chain = root / "stages/01b_chain-table/output"
        chain.mkdir(parents=True)
        (chain / "s-chain.md").write_text(
            "| `Web/request[Routed]` | `Web.request` | `x` | `Routed` | e |\n",
            encoding="utf-8")

    def test_legacy_trace_warns_and_enabled_flow_test_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "UC-99-x"
            self._feature(root)
            tests = Path(temporary) / "tests"
            tests.mkdir()
            (tests / "LoginFlowTest.java").write_text(
                "class LoginFlowTest { @Test void f() {} }\n", encoding="utf-8")
            result = run(str(QG / "verify_close_evidence.py"),
                         "--feature-root", str(root),
                         "--test-source-root", str(tests))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("legacy", result.stdout)
            self.assertIn("adapter integration test present", result.stdout)


if __name__ == "__main__":
    unittest.main()


class ParityConstantsSiblingLayoutTests(unittest.TestCase):
    """Regression (conduit rebuild UC-01 finding): derived repos whose concept
    constants live in sibling `concepts/` packages — the symbol table must
    walk the Java module root, not the syncs dir alone."""

    def test_strict_trigger_resolves_constants_in_sibling_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "app"
            # Module-root layout: concepts package + syncs package siblings.
            concept_dir = root / "java/src/main/java/com/example/concepts"
            sync_dir = root / "syncs"
            concept_dir.mkdir(parents=True)
            sink_sync = root / "java/src/main/java/com/example/syncs"
            sink_sync.mkdir(parents=True)
            spec_name = "WebRespondForWidgetWhenWebRequestRouted"
            contract_dir = root / "features/UC-01-widget/stages/03_syncs/output"
            contract_dir.mkdir(parents=True)
            write(contract_dir / f"{spec_name}.sync.md",
                  "sync " + spec_name + "\n\n## Rule\n\nwhen {\n"
                  "    Web/request: [ x: ?x ] => [ Routed ]\n}\nthen {\n"
                  "    Inventory/lend: [ x: ?x ]\n}\n")
            write(sink_sync / f"{spec_name}.java",
                  "final class C {\n"
                  "    SyncRule rule() {\n"
                  '        return rule("' + spec_name + '")\n'
                  "            .when(Web.NAME, Web.REQUEST, \"Routed\")\n"
                  "            .then(invoke(Inventory.NAME, Inventory.LEND, args()));\n"
                  "    }\n}\n")
            write(concept_dir / "Web.java",
                  "final class Web {\n"
                  "    public static final String NAME = \"Web\";\n"
                  "    public static final String REQUEST = \"request\";\n}\n")
            write(concept_dir / "Inventory.java",
                  "final class Inventory {\n"
                  "    public static final String NAME = \"Inventory\";\n"
                  "    public static final String LEND = \"lend\";\n}\n")
            result = run(str(QG / "verify_sync_implementation_parity.py"),
                         "--sync-dir", str(contract_dir),
                         "--sync-impl-dir", str(sink_sync),
                         "--strict-trigger")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

