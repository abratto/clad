#!/usr/bin/env python3
"""Regression coverage for iterative-change record selection."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))

import verify_iterative_change_readiness as readiness  # noqa: E402


def run(*args):
    return subprocess.run(
        [sys.executable, str(QUALITY_GATE / "verify_iterative_change_readiness.py"), *args],
        cwd=REPO_ROOT, capture_output=True, text=True)


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

    def test_canonical_corpus_concept_is_iterative_scope(self):
        """Editing a canonical corpus spec must require a `_changes/` record,
        exactly like a per-feature concept spec (M1 completeness)."""
        self.assertTrue(readiness.in_iterative_scope(
            "features/_system/concepts/PasswordAuth.concept.md"))
        self.assertTrue(readiness.in_iterative_scope(
            "features/UC-01-a/stages/02_concepts/output/C.concept.md"))
        self.assertFalse(readiness.in_iterative_scope(
            "features/_system/concepts-catalog.md"))


class NewStageWorkExemptionTests(unittest.TestCase):
    """An uncommitted stage artefact whose gate is not yet approved is the
    feature's own output, not an edit of a gated artefact, so `advance →
    commit → verify` is not required (Item 3, readiness-guard ordering)."""

    def _feature(self, root, resume):
        feature = root / "UC-01-a"
        (feature / "stages/03_syncs/output").mkdir(parents=True)
        (feature / "stages/02_concepts/output").mkdir(parents=True)
        if resume is not None:
            (feature / "RESUME.md").write_text(resume, encoding="utf-8")
        return feature

    def test_ungated_stage_artefact_is_new_stage_work(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(Path(temporary),
                                    "# RESUME\n\n- **Gate 1 (Requirements):** `approved`\n")
            path = "features/UC-01-a/stages/03_syncs/output/X.sync.md"
            self.assertTrue(readiness.is_new_stage_work(path, str(feature)))

    def test_gated_stage_artefact_is_not_new_stage_work(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(
                Path(temporary),
                "# RESUME\n\n- **Gate 2 (Architecture):** `approved`\n")
            path = "features/UC-01-a/stages/03_syncs/output/X.sync.md"
            self.assertFalse(readiness.is_new_stage_work(path, str(feature)))

    def test_corpus_and_unmapped_paths_are_never_exempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(Path(temporary), "# RESUME\n")
            self.assertFalse(readiness.is_new_stage_work(
                "features/_system/concepts/C.concept.md", str(feature)))
            self.assertFalse(readiness.is_new_stage_work(
                "app/src/main/java/x/syncs/Y.java", str(feature)))

    def test_missing_resume_is_not_exempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(Path(temporary), None)
            path = "features/UC-01-a/stages/03_syncs/output/X.sync.md"
            self.assertFalse(readiness.is_new_stage_work(path, str(feature)))

    def test_cli_exempts_ungated_stage_output_without_a_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(Path(temporary),
                                    "# RESUME\n\n- **Gate 1 (Requirements):** `approved`\n")
            changed = Path(temporary) / "changed.txt"
            changed.write_text(
                "features/UC-01-a/stages/03_syncs/output/X.sync.md\n",
                encoding="utf-8")
            result = run("--feature", str(feature),
                         "--changed-files-file", str(changed))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("own stage output", result.stdout)

    def test_cli_still_requires_a_record_for_a_gated_edit(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(
                Path(temporary),
                "# RESUME\n\n- **Gate 2 (Architecture):** `approved`\n")
            changed = Path(temporary) / "changed.txt"
            changed.write_text(
                "features/UC-01-a/stages/03_syncs/output/X.sync.md\n",
                encoding="utf-8")
            result = run("--feature", str(feature),
                         "--changed-files-file", str(changed))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no active", result.stdout)


if __name__ == "__main__":
    unittest.main()