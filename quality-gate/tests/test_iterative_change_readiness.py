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


class ActiveChangeSelectorTests(unittest.TestCase):
    """One selector for "the active change": `Status: active`, not newest mtime."""

    def _record(self, feature, name, status, stage="02"):
        changes = feature / "_changes"
        changes.mkdir(parents=True, exist_ok=True)
        (changes / name).write_text(
            f"- **Status:** `{status}`\n"
            f"- **Earliest re-entry stage:** `{stage}`\n", encoding="utf-8")

    def test_selects_by_status_not_mtime(self):
        import verify_stage_sequence as vss
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-02-x"
            feature.mkdir()
            self._record(feature, "closed.md", "closed", "03b")
            self._record(feature, "active.md", "active", "02")

            records = vss.active_change_records(str(feature))

            self.assertEqual([s for s, _ in records], ["02"])
            self.assertEqual(vss.active_reentry_change(str(feature))[0], "02")

    def test_two_active_records_are_visible_and_the_single_selector_is_none(self):
        import verify_stage_sequence as vss
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-02-x"
            feature.mkdir()
            self._record(feature, "a.md", "active", "02")
            self._record(feature, "b.md", "active", "03b")

            self.assertEqual(len(vss.active_change_records(str(feature))), 2)
            self.assertIsNone(vss.active_reentry_change(str(feature)))


class ReentryProgressTests(unittest.TestCase):
    """The re-entry stage must be recorded as re-derived (content), not by a
    stage receipt's mtime (non-deterministic across clones/rebase)."""

    def _record(self, feature, done):
        import json
        changes = feature / "_changes"
        changes.mkdir(parents=True, exist_ok=True)
        change = changes / "reentry.md"
        change.write_text(
            "# `reentry` — iterative change\n\n"
            "- **Change category:** `structural`\n"
            "- **Status:** `active`\n"
            "- **Earliest re-entry stage:** `02`\n"
            "- **Why:** x\n\n"
            "This change is governed by `methodology/core/ITERATIVE_CHANGES.md`.\n\n"
            "## Artefact-impact matrix\n\n"
            "| Artefact | Touched? | How |\n|---|---|---|\n"
            "| Concept(s) | `yes` | x |\n"
            "| Sync(s) | `no` | x |\n"
            "| Contract slices | `no` | x |\n"
            "| Flow tests | `no` | x |\n"
            "| Concept tests | `no` | x |\n"
            "| Sync tests | `no` | x |\n"
            "| Production code | `no` | x |\n\n"
            "## Re-derivation order\n\n1. Re-open Stage 02 — x\n",
            encoding="utf-8")
        (changes / "reentry.progress.json").write_text(
            json.dumps({"done": done}), encoding="utf-8")
        return change

    def test_reentry_stage_must_be_recorded_as_re_derived(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-02-x"
            feature.mkdir()
            change = self._record(feature, done=[])
            failures = readiness.validate_change_file(str(change), False)
            self.assertTrue(
                any("not recorded as re-derived" in message
                    for _, message in failures), failures)

    def test_reentry_stage_recorded_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-02-x"
            feature.mkdir()
            change = self._record(feature, done=["02"])
            self.assertEqual(readiness.validate_change_file(str(change), False), [])

    def test_legacy_acceptance_tests_row_is_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-02-x"
            feature.mkdir()
            change = self._record(feature, done=["02"])
            text = change.read_text(encoding="utf-8").replace("Flow tests",
                                                              "Acceptance tests")
            change.write_text(text, encoding="utf-8")
            self.assertEqual(readiness.validate_change_file(str(change), False), [])


class SystemCorpusMaintenanceRouteTests(unittest.TestCase):
    """A system-scope corpus edit is governed by the maintenance route (R22),
    not a per-feature `_changes/` record no feature can own."""

    def test_corpus_artefacts_match_the_system_scope(self):
        self.assertTrue(readiness.SYSTEM_CORPUS_RE.match(
            "features/_system/concepts/Foo.concept.md"))
        self.assertTrue(readiness.SYSTEM_CORPUS_RE.match(
            "features/_system/concepts/Foo.data-model.md"))
        self.assertTrue(readiness.SYSTEM_CORPUS_RE.match(
            "features/_system/concepts/Foo.contract.md"))
        self.assertFalse(readiness.SYSTEM_CORPUS_RE.match(
            "features/UC-01-a/stages/02_concepts/output/Foo.concept.md"))

    def test_corpus_only_edit_defers_to_the_maintenance_route(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-01-a"
            feature.mkdir()
            changed = Path(temporary) / "changed.txt"
            changed.write_text(
                "features/_system/concepts/Foo.concept.md\n", encoding="utf-8")

            result = run("--feature", str(feature),
                         "--changed-files-file", str(changed))

            # With no active maintenance record the maintenance gate refuses, and
            # the readiness guard surfaces that route (not a feature record).
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("maintenance route", result.stdout)


if __name__ == "__main__":
    unittest.main()