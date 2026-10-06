#!/usr/bin/env python3
"""Regression coverage for Stage 03a's derived review views
(maintenance change `ad-review-evidence`): generate_review_views.py's two
views, their drift check, the manifest listing, and the 03a wiring."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "quality-gate" / "generate_review_views.py"
UC00 = REPO_ROOT / "examples" / "UC-00-login"

sys.path.insert(0, str(REPO_ROOT / "quality-gate"))
import artifact_parsers as ap  # noqa: E402
import clad_stages as cs  # noqa: E402


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          cwd=REPO_ROOT, capture_output=True, text=True)


class GeneratedViewTests(unittest.TestCase):

    def test_worked_example_views_are_current(self):
        proc = run("--feature", str(UC00), "--check")
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("PASS  review views current", proc.stdout)

    def test_regeneration_is_deterministic(self):
        first = run("--feature", str(UC00), "--write")
        second = run("--feature", str(UC00), "--check")
        self.assertEqual(0, first.returncode)
        self.assertEqual(0, second.returncode)

    def test_stale_view_fails_the_check(self):
        matrix = UC00 / "stages" / "03a_dependency-review" / "output" / "concept-matrix.md"
        original = matrix.read_text()
        try:
            matrix.write_text(original + "\nhand edit\n")
            proc = run("--feature", str(UC00), "--check")
        finally:
            matrix.write_text(original)
        self.assertEqual(1, proc.returncode, "stale views must block")
        self.assertIn("concept-matrix.md: stale", proc.stdout)
        self.assertIn("--write", proc.stdout)

    def test_missing_inputs_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run("--feature", tmp)
        self.assertEqual(0, proc.returncode)
        self.assertIn("SKIP", proc.stdout)


class ManifestAndWiringTests(unittest.TestCase):

    def test_manifest_lists_both_views_at_03a(self):
        expected = ap.expected_stage_outputs(str(UC00))["03a"]
        self.assertIn("concept-matrix.md", expected)
        self.assertIn("sync-information-profile.md", expected)
        self.assertIn("pattern-d-summary.md", expected)

    def test_stage03a_carries_the_drift_check(self):
        stage = next(s for s in cs.STAGES if s.id == "03a")
        names = {c.name for c in stage.checks}
        self.assertIn("review_views_current", names)

    def test_drift_check_requires_both_views(self):
        stage = next(s for s in cs.STAGES if s.id == "03a")
        check = next(c for c in stage.checks if c.name == "review_views_current")
        requires = check.requires(str(UC00))
        self.assertEqual(
            sorted(os.path.basename(r) for r in requires),
            ["concept-matrix.md", "sync-information-profile.md"])
        self.assertTrue(all(os.path.isfile(r) for r in requires),
                        "the worked example carries both views")


if __name__ == "__main__":
    unittest.main()
