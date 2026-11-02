#!/usr/bin/env python3
"""Stage 05 trace skeleton generation."""

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))

import generate_trace as gt  # noqa: E402


class TraceGenerationTests(unittest.TestCase):

    def test_render_has_every_scenario_and_expected_chain(self):
        feature = REPO_ROOT / "examples/UC-00-login"
        text = gt.render(
            str(feature),
            str(feature / "stages/01_usecase/output/usecase.md"),
            str(feature / "stages/01b_chain-table/output"),
            {})
        self.assertEqual(text.count("\n## "), 4)
        self.assertIn("Web.request[ROUTED]", text)
        self.assertIn("PasswordAuth/check[OK]", text)
        self.assertIn("<TODO: runtime evidence>", text)

    def test_branched_chain_emits_a_main_section_and_subcase(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-01-branch"
            usecase = feature / "stages/01_usecase/output/usecase.md"
            chain = feature / "stages/01b_chain-table/output"
            usecase.parent.mkdir(parents=True)
            chain.mkdir(parents=True)
            usecase.write_text(
                "# UC-01 branch\n\n## Scenarios\n\n### Scenario: branch\n\n",
                encoding="utf-8")
            (chain / "branch-chain.md").write_text(
                "| # | When | Then | Inputs | Outcome | Why |\n"
                "|---|---|---|---|---|---|\n"
                "| 1 | `Web/request[POST /x]` | `Web.request` | `x` | `ROUTED` | entry |\n"
                "| 2 | `Web.request[ROUTED]` | `Claim.validate` | `x` | `OK` | valid |\n"
                "| 3 | `Web.request[ROUTED]` | `Claim.validate` | `x` | `REFUSED` | invalid |\n"
                "| 4 | `Claim.validate[OK]` | `Claim.submit` | `x` | `ACCEPTED` | write |\n"
                "| 5 | `Claim.submit[ACCEPTED]` | `Web.respond[201]` | `201` | `SENT` | ok |\n"
                "| 6 | `Claim.validate[REFUSED]` | `Web.respond[400]` | `400` | `SENT` | bad |\n",
                encoding="utf-8")
            text = gt.render(str(feature), str(usecase), str(chain), {})
        self.assertEqual(text.count("\n## "), 1)
        self.assertIn("### branch — sub-case", text)
        self.assertIn("Claim/validate[OK]", text)
        self.assertIn("Claim/validate[REFUSED]", text)

    def test_observations_fill_runtime_evidence(self):
        feature = REPO_ROOT / "examples/UC-00-login"
        text = gt.render(
            str(feature),
            str(feature / "stages/01_usecase/output/usecase.md"),
            str(feature / "stages/01b_chain-table/output"),
            {"successful-login": {"runtime": ["Web.request[ROUTED]"],
                                  "test": "LoginFlowTest.successfulLogin",
                                  "verdict": "covered"}})
        self.assertIn("LoginFlowTest.successfulLogin", text)
        self.assertIn("**Verdict:** covered", text)


if __name__ == "__main__":
    unittest.main()
