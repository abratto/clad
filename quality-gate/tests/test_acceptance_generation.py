#!/usr/bin/env python3
"""Acceptance Spec skeleton generation."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))

import generate_acceptance_spec as gas  # noqa: E402


class AcceptanceGenerationTests(unittest.TestCase):

    def test_render_covers_scenarios_and_token_chains(self):
        feature = REPO_ROOT / "examples/UC-00-login"
        text = gas.render(
            str(feature),
            str(feature / "stages/01_usecase/output/usecase.md"),
            str(feature / "stages/01b_chain-table/output"),
            "UC-00 login")
        self.assertEqual(text.count("## Scenario:"), 4)
        self.assertIn("## Scenario: successful-login", text)
        self.assertIn("PasswordAuth.check[OK]", text)
        self.assertIn("Web.respond[SENT]", text)
        self.assertIn("**Test:** `<TestClass>.<testMethod>`", text)

    def test_branched_chain_emits_a_main_scenario_and_subcases(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-01-branch"
            usecase = feature / "stages/01_usecase/output/usecase.md"
            chain = feature / "stages/01b_chain-table/output"
            usecase.parent.mkdir(parents=True)
            chain.mkdir(parents=True)
            usecase.write_text(
                "# UC-01 branch\n\n## Scenarios\n\n"
                "### Scenario: branch\n\n"
                "- **Postconditions — Success:**\n  - a claim exists\n",
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
            text = gas.render(str(feature), str(usecase), str(chain), "Branch")
        self.assertEqual(text.count("## Scenario:"), 1)
        self.assertIn("## Scenario: branch", text)
        self.assertIn("### Sub-case", text)
        self.assertIn("Claim.validate[OK]", text)
        self.assertIn("Claim.validate[REFUSED]", text)
        self.assertIn("Web.respond[SENT]", text)

    def test_write_refuses_to_clobber_without_force(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-00-login"
            shutil.copytree(REPO_ROOT / "examples/UC-00-login", feature)
            self.assertNotEqual(gas.main(["--feature", str(feature), "--write"]), 0)
            self.assertEqual(
                gas.main(["--feature", str(feature), "--write", "--force"]), 0)


if __name__ == "__main__":
    unittest.main()
