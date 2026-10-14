#!/usr/bin/env python3
"""Regression coverage for verify_chain_outcomes.py.

A chain row's `Concept.action[Completion]` must be declared by that concept's
spec. The UC-08 shape — a `reused` read action invoked on a failure branch its
canonical spec does not declare — must fail with the "propose an `extends`"
remedy; a completion the spec declares must pass.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"


def run(*args):
    return subprocess.run(
        [sys.executable, str(QG / "verify_chain_outcomes.py"), *args],
        cwd=REPO_ROOT, capture_output=True, text=True)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


RESP_MAP = """# Responsibility map

## Concepts

| Concept | Origin | Owned state (one line) | Owned actions | Notes |
|---|---|---|---|---|
| `GuidelineRules` | `reused:UC-07-maintain-guideline-rules` | `f: Id -> T` | `publishedLineages` | — |
"""


def chain(when_cell):
    return ("# Chain table\n\n"
            "| # | When | Then | Inputs | Outcome | Why this step |\n"
            "|---|---|---|---|---|---|\n"
            f"| 1 | `{when_cell}` | `Web.respond` | x | `SENT` | step |\n")


def spec(actions):
    return ("concept GuidelineRules [RuleSetLineageId]\n"
            "purpose\n    to publish rule-set lineages\n\n"
            "## Actions\n\n```\n" + actions + "\n```\n")


class ChainOutcomeTests(unittest.TestCase):

    def _world(self, tmp, when_cell, canonical_actions):
        root = Path(tmp)
        resp = root / "resp.md"
        write(resp, RESP_MAP)
        chain_dir = root / "01b"
        write(chain_dir / "scenario-chain.md", chain(when_cell))
        corpus = root / "concepts"
        write(corpus / "GuidelineRules.concept.md", spec(canonical_actions))
        return str(resp), str(chain_dir), str(corpus)

    def test_reused_concept_missing_completion_routes_to_01a(self):
        # `publishedLineages` only has an `OK` completion; the chain triggers on
        # a `REFUSED` the canonical concept never emits (the UC-08 shape).
        with tempfile.TemporaryDirectory() as tmp:
            resp, chain_dir, corpus = self._world(
                tmp, "GuidelineRules/publishedLineages[REFUSED]",
                "publishedLineages [ ] => [ OK ]\n")
            result = run("--resp-map", resp, "--chain-dir", chain_dir,
                         "--concept-dir", corpus)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Propose an `extends`", result.stdout)
            self.assertIn("reopen Stage 01a", result.stdout)

    def test_declared_completion_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            resp, chain_dir, corpus = self._world(
                tmp, "GuidelineRules/publishedLineages[OK]",
                "publishedLineages [ ] => [ OK ]\n")
            result = run("--resp-map", resp, "--chain-dir", chain_dir,
                         "--concept-dir", corpus)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS", result.stdout)

    def test_undeclared_action_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            resp, chain_dir, corpus = self._world(
                tmp, "GuidelineRules.nonexistent[OK]",
                "publishedLineages [ ] => [ OK ]\n")
            result = run("--resp-map", resp, "--chain-dir", chain_dir,
                         "--concept-dir", corpus)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("declares no such action", result.stdout)


if __name__ == "__main__":
    unittest.main()
