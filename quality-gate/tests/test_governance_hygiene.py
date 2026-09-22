#!/usr/bin/env python3
"""Regression coverage for verify_governance_hygiene.py (advisory)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"


def run(*args):
    return subprocess.run(
        [sys.executable, str(QG / "verify_governance_hygiene.py"), *args],
        cwd=REPO_ROOT, capture_output=True, text=True)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class GovernanceHygieneTests(unittest.TestCase):

    def test_clean_tree_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "maintenance/change.md", "- **Status:** `closed`\n")
            write(root / "features/UC-01-x/RESUME.md",
                  "- **Next stage:** `None — feature complete`\n")
            result = run("--features-dir", str(root / "features"),
                         "--maintenance-dir", str(root / "maintenance"))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS", result.stdout)

    def test_two_active_maintenance_records_warn(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "maintenance/a.md", "- **Status:** `active`\n")
            write(root / "maintenance/b.md", "- **Status:** `active`\n")
            result = run("--features-dir", str(root / "features"),
                         "--maintenance-dir", str(root / "maintenance"))
            self.assertEqual(result.returncode, 0, "advisory must not block")
            self.assertIn("WARN", result.stdout)
            self.assertIn("active", result.stdout)

    def test_active_record_on_a_complete_feature_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature = root / "features/UC-01-x"
            write(feature / "RESUME.md", "- **Next stage:** `None — feature complete`\n")
            write(feature / "_changes/stale.md", "- **Status:** `active`\n")
            result = run("--features-dir", str(root / "features"),
                         "--maintenance-dir", str(root / "maintenance"))
            self.assertEqual(result.returncode, 0, "advisory must not block")
            self.assertIn("WARN", result.stdout)
            self.assertIn("feature complete", result.stdout)

    def test_multiple_active_changes_on_one_feature_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature = root / "features/UC-01-x"
            write(feature / "RESUME.md", "- **Current stage:** `Stage 03 — Syncs`\n")
            write(feature / "_changes/a.md", "- **Status:** `active`\n")
            write(feature / "_changes/b.md", "- **Status:** `active`\n")
            result = run("--features-dir", str(root / "features"),
                         "--maintenance-dir", str(root / "maintenance"))
            self.assertEqual(result.returncode, 0, "advisory must not block")
            self.assertIn("WARN", result.stdout)
            self.assertIn("exactly one", result.stdout)


if __name__ == "__main__":
    unittest.main()
