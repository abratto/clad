#!/usr/bin/env python3
"""Regression coverage for iterative-change record selection."""

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))

import verify_iterative_change_readiness as readiness  # noqa: E402


class IterativeChangeReadinessTests(unittest.TestCase):

    def write_change(self, feature, name, status):
        changes = feature / "_changes"
        changes.mkdir(exist_ok=True)
        path = changes / name
        path.write_text(f"- **Status:** `{status}`\n", encoding="utf-8")
        return path

    def test_selects_the_only_active_record_among_historical_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-02-selection"
            feature.mkdir()
            self.write_change(feature, "old-closed.md", "closed")
            self.write_change(feature, "old-superseded.md", "superseded")
            active = self.write_change(feature, "current.md", "active")

            selected, failures = readiness.select_change_file(str(feature), "")

            self.assertEqual(selected, str(active))
            self.assertEqual(failures, [])

    def test_rejects_when_no_active_record_exists(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-02-selection"
            feature.mkdir()
            self.write_change(feature, "old.md", "superseded")

            selected, failures = readiness.select_change_file(str(feature), "")

            self.assertEqual(selected, "")
            self.assertEqual(len(failures), 1)
            self.assertIn("no active", failures[0][1])

    def test_rejects_when_multiple_active_records_exist(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-02-selection"
            feature.mkdir()
            self.write_change(feature, "first.md", "active")
            self.write_change(feature, "second.md", "active")

            selected, failures = readiness.select_change_file(str(feature), "")

            self.assertEqual(selected, "")
            self.assertEqual(len(failures), 1)
            self.assertIn("multiple active", failures[0][1])

    def test_explicit_path_remains_an_operator_override(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-02-selection"
            feature.mkdir()
            historical = self.write_change(feature, "old.md", "superseded")

            selected, failures = readiness.select_change_file(str(feature), str(historical))

            self.assertEqual(selected, str(historical))
            self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()