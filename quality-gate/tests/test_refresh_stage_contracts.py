#!/usr/bin/env python3
"""Regression coverage for refresh_stage_contracts.py (D1: stale feature-local
stage contracts)."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"


def run(*args):
    return subprocess.run(
        [sys.executable, str(QG / "refresh_stage_contracts.py"), *args],
        cwd=REPO_ROOT, capture_output=True, text=True)


class RefreshStageContractsTests(unittest.TestCase):

    def _feature(self, tmp):
        feature = Path(tmp) / "UC-01-x"
        shutil.copytree(REPO_ROOT / "templates/feature-skeleton", feature)
        return feature

    def test_a_stale_verify_section_is_reported_then_refreshed(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = self._feature(tmp)
            ctx = feature / "stages" / "02_concepts" / "CONTEXT.md"
            ctx.write_text(ctx.read_text(encoding="utf-8").replace(
                "## Verify", "## Verify\n\nSTALE-MARKER\n", 1), encoding="utf-8")

            check = run("--feature", str(feature), "--check")
            self.assertIn("STALE", check.stdout)
            self.assertIn("02_concepts", check.stdout)

            run("--feature", str(feature), "--write")
            self.assertNotIn("STALE-MARKER", ctx.read_text(encoding="utf-8"))

    def test_a_current_feature_reports_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = self._feature(tmp)
            result = run("--feature", str(feature), "--check")
            self.assertEqual(result.returncode, 0)
            self.assertIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
