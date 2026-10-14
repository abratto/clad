#!/usr/bin/env python3
"""Regression coverage for create_consent.py (the remodel consent scaffolder)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"


def run(*args):
    return subprocess.run(
        [sys.executable, str(QG / "create_consent.py"), *args],
        cwd=REPO_ROOT, capture_output=True, text=True)


class CreateConsentTests(unittest.TestCase):

    def _world(self, tmp):
        root = Path(tmp) / "features"
        (root / "UC-06-x").mkdir(parents=True)
        corpus = root / "_system" / "concepts"
        corpus.mkdir(parents=True)
        (corpus / "DrinkLogging.concept.md").write_text(
            "concept DrinkLogging [AccountId]\n", encoding="utf-8")
        return str(root / "UC-06-x"), corpus

    def test_writes_a_named_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature, corpus = self._world(tmp)
            result = run("--feature", feature, "--concept", "DrinkLogging",
                         "--consenting", "UC-04-log-drink")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            receipt = (corpus / "_remodel-consent"
                       / "DrinkLogging-UC-04-log-drink.md")
            self.assertTrue(receipt.is_file())
            self.assertIn("UC-04-log-drink", receipt.read_text(encoding="utf-8"))

    def test_existing_receipt_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature, corpus = self._world(tmp)
            run("--feature", feature, "--concept", "DrinkLogging",
                "--consenting", "UC-04-log-drink")
            result = run("--feature", feature, "--concept", "DrinkLogging",
                         "--consenting", "UC-04-log-drink")
            self.assertEqual(result.returncode, 0)
            self.assertIn("SKIP", result.stdout)


if __name__ == "__main__":
    unittest.main()
