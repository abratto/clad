#!/usr/bin/env python3
"""Regression coverage for D3 (distinct outcomes) and D9/D26 (outcome casing)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
DISTINCT = QG / "verify_distinct_outcomes.py"
CASING = QG / "verify_outcome_casing.py"


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *map(str, args)],
                          cwd=REPO_ROOT, capture_output=True, text=True)


def write_chain(chain_dir, name, rows):
    chain_dir.mkdir(parents=True, exist_ok=True)
    body = ["# Chain table", "",
            "| # | When | Then | Inputs | Outcome | Why this step |",
            "|---|---|---|---|---|---|"]
    for num, when, then, outcome in rows:
        body.append(f"| {num} | `{when}` | `{then}` | `x` | `{outcome}` | e |")
    (chain_dir / f"{name}-chain.md").write_text("\n".join(body) + "\n",
                                                encoding="utf-8")


class DistinctOutcomesTests(unittest.TestCase):

    def test_two_statuses_from_one_token_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            chain = Path(tmp) / "chain"
            write_chain(chain, "enrol", [
                ("1", "Web/request[POST /enrol]", "Web.request", "ROUTED"),
                ("2", "Web.request[ROUTED]", "Member.check", "OK"),
                ("3", "Member.check[REFUSED]", "Web.respond[400]", "SENT"),
                ("4", "Member.check[REFUSED]", "Web.respond[409]", "SENT"),
            ])
            r = run(DISTINCT, "--chain-dir", chain)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_distinct_tokens_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            chain = Path(tmp) / "chain"
            write_chain(chain, "enrol", [
                ("1", "Web/request[POST /enrol]", "Web.request", "ROUTED"),
                ("2", "Web.request[ROUTED]", "Member.checkName", "OK"),
                ("3", "Member.checkName[REFUSED]", "Web.respond[400]", "SENT"),
                ("4", "Member.checkName[OK]", "Member.checkRef", "OK"),
                ("5", "Member.checkRef[REFUSED]", "Web.respond[409]", "SENT"),
            ])
            r = run(DISTINCT, "--chain-dir", chain)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class OutcomeCasingTests(unittest.TestCase):

    def _feature(self, tmp):
        feature = Path(tmp) / "features/UC-01-x"
        (feature / "stages/01b_chain-table/output").mkdir(parents=True)
        return feature

    def test_pascal_chain_outcome_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = self._feature(tmp)
            write_chain(feature / "stages/01b_chain-table/output", "x", [
                ("1", "Web/request[POST /x]", "Web.request", "Routed"),
            ])
            r = run(CASING, "--feature", feature)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_screaming_chain_outcome_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = self._feature(tmp)
            write_chain(feature / "stages/01b_chain-table/output", "x", [
                ("1", "Web/request[POST /x]", "Web.request", "ROUTED"),
            ])
            r = run(CASING, "--feature", feature)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_spec_flow_token_casing_is_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = self._feature(tmp)
            concept_dir = feature / "stages/02_concepts/output"
            concept_dir.mkdir(parents=True)
            (concept_dir / "Member.concept.md").write_text(
                "concept Member\n\n## Actions\n\n"
                "```\ncheck [ ref: String ] => [ Ok ]\n"
                "    flow token: { action: \"Member.check\", outcome: \"Ok\" }\n```\n",
                encoding="utf-8")
            bad = run(CASING, "--feature", feature)
            self.assertEqual(bad.returncode, 1, bad.stdout + bad.stderr)
            (concept_dir / "Member.concept.md").write_text(
                "concept Member\n\n## Actions\n\n"
                "```\ncheck [ ref: String ] => [ OK ]\n"
                "    flow token: { action: \"Member.check\", outcome: \"OK\" }\n```\n",
                encoding="utf-8")
            good = run(CASING, "--feature", feature)
            self.assertEqual(good.returncode, 0, good.stdout + good.stderr)


if __name__ == "__main__":
    unittest.main()
