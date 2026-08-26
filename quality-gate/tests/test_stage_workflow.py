#!/usr/bin/env python3
"""Regression coverage for canonical stage routing."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))

import advance  # noqa: E402
import clad_stages as stages  # noqa: E402
import verify_artefacts  # noqa: E402


class StageWorkflowTests(unittest.TestCase):

    def make_feature(self, temporary):
        feature = Path(temporary) / "UC-01-workflow"
        shutil.copytree(REPO_ROOT / "templates/feature-skeleton", feature)
        return feature

    def populate_through(self, feature, stage_id):
        for stage in stages.STAGES:
            output = Path(stage.output_dir(str(feature)))
            output.mkdir(parents=True, exist_ok=True)
            (output / "evidence.md").write_text(stage.id, encoding="utf-8")
            if stage.id == stage_id:
                return

    def sequence_result(self, feature, through):
        return subprocess.run(
            [
                sys.executable,
                str(QUALITY_GATE / "verify_stage_sequence.py"),
                "--feature",
                str(feature),
                "--through",
                through,
                "--no-gates",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )

    def test_fresh_skeleton_routes_through_each_red_green_stage(self):
        expected_stage_ids = [
            "01", "01a", "01b", "02", "03", "03a", "03b", "04a", "04b",
            "04c", "04d-red", "04d-green", "04e-red", "04e-green", "05",
        ]
        self.assertEqual([stage.id for stage in stages.STAGES], expected_stage_ids)

        with tempfile.TemporaryDirectory() as temporary:
            feature = self.make_feature(temporary)
            resume = feature / "RESUME.md"
            resume.write_text(
                resume.read_text(encoding="utf-8").replace("`pending`", "`approved`"),
                encoding="utf-8",
            )

            for stage in stages.STAGES:
                output = Path(stage.output_dir(str(feature)))
                output.mkdir(parents=True, exist_ok=True)
                (output / "evidence.md").write_text(stage.id, encoding="utf-8")
                self.assertEqual(advance.determine_stage(str(feature), None).id, stage.id)

                # Bind each approved gate to the current content so the hash
                # check passes (approve_gate.py --baseline records the hash
                # without changing the already-`approved` status).
                if stage.gate_after is not None:
                    baseline = subprocess.run(
                        [
                            sys.executable,
                            str(QUALITY_GATE / "approve_gate.py"),
                            "--feature",
                            str(feature),
                            "--gate",
                            str(stage.gate_after),
                            "--baseline",
                        ],
                        cwd=REPO_ROOT,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(baseline.returncode, 0,
                                     baseline.stdout + baseline.stderr)

                result = subprocess.run(
                    [
                        sys.executable,
                        str(QUALITY_GATE / "verify_stage_sequence.py"),
                        "--feature",
                        str(feature),
                        "--through",
                        stage.id,
                        "--no-gates",
                    ],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            advance_result = subprocess.run(
                [
                    sys.executable,
                    str(QUALITY_GATE / "advance.py"),
                    "--feature",
                    str(feature),
                    "--stage",
                    "04d-green",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(advance_result.returncode, 0,
                             advance_result.stdout + advance_result.stderr)
            self.assertIn("04e_sync-tdd/04e_red-tests/CONTEXT.md",
                          advance_result.stdout)

    def test_completed_pre_split_parent_stage_evidence_is_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.make_feature(temporary)
            self.populate_through(feature, "04c")
            concept_output = feature / "stages/04_implement/04d_concept-tdd/output"
            sync_output = feature / "stages/04_implement/04e_sync-tdd/output"
            concept_output.mkdir(parents=True, exist_ok=True)
            sync_output.mkdir(parents=True, exist_ok=True)
            (concept_output / "concept-tdd.md").write_text("legacy concept evidence")
            (sync_output / "sync-tdd.md").write_text("legacy sync evidence")
            output = Path(stages.stage_by_id("05").output_dir(str(feature)))
            output.mkdir(parents=True, exist_ok=True)
            (output / "verification.md").write_text("legacy completed flow")

            result = self.sequence_result(feature, "05")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_historical_green_summary_can_supply_immediately_prior_red_stage(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.make_feature(temporary)
            self.populate_through(feature, "04c")
            green = Path(stages.stage_by_id("04d-green").output_dir(str(feature)))
            green.mkdir(parents=True, exist_ok=True)
            (green / "historical-green-summary.md").write_text(
                "<!-- CLAD historical-green-summary: includes 04d-red evidence -->\n"
                "Legacy green implementation summary.",
                encoding="utf-8",
            )

            result = self.sequence_result(feature, "04d-green")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_active_reentry_caps_artefact_target_before_historical_stage_five(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.make_feature(temporary)
            self.populate_through(feature, "05")
            changes = feature / "_changes"
            changes.mkdir(exist_ok=True)
            (changes / "concept-correction.md").write_text(
                "- **Status:** `active`\n"
                "- **Change category:** `structural`\n"
                "- **Earliest re-entry stage:** `04d-red`\n"
                "- **Why:** correct the concept test derivation\n",
                encoding="utf-8",
            )
            reentry_output = Path(stages.stage_by_id("04d-red").output_dir(str(feature)))
            reentry_output.mkdir(parents=True, exist_ok=True)
            (reentry_output / "new-red-evidence.md").write_text("active re-entry")
            green_output = Path(stages.stage_by_id("04d-green").output_dir(str(feature)))
            green_output.mkdir(parents=True, exist_ok=True)
            (green_output / "new-green-evidence.md").write_text("active re-entry")

            self.assertEqual(verify_artefacts._current_stage(str(feature)).id, "04d-green")

    def test_new_partial_child_stage_history_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.make_feature(temporary)
            self.populate_through(feature, "04c")
            green = Path(stages.stage_by_id("04d-green").output_dir(str(feature)))
            green.mkdir(parents=True, exist_ok=True)
            (green / "implementation.md").write_text("new child work")

            result = self.sequence_result(feature, "04d-green")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("04d-red", result.stdout)

    def test_legacy_parent_evidence_cannot_mask_partial_child_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.make_feature(temporary)
            self.populate_through(feature, "04c")
            parent = feature / "stages/04_implement/04d_concept-tdd/output"
            (parent / "concept-tdd.md").write_text("legacy parent evidence")
            green = Path(stages.stage_by_id("04d-green").output_dir(str(feature)))
            (green / "implementation.md").write_text("partial child work")

            result = self.sequence_result(feature, "04d-green")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("04d-red", result.stdout)


if __name__ == "__main__":
    unittest.main()

class GateContentBindingTests(unittest.TestCase):
    """A gate approval is bound to a content hash of its stages."""

    def _approved_feature(self, feature):
        resume = feature / "RESUME.md"
        resume.write_text(
            resume.read_text(encoding="utf-8").replace("`pending`", "`approved`"),
            encoding="utf-8",
        )
        for stage in stages.STAGES:
            output = Path(stage.output_dir(str(feature)))
            output.mkdir(parents=True, exist_ok=True)
            (output / "evidence.md").write_text(stage.id, encoding="utf-8")

    def _gate_sequence(self, feature, through):
        return subprocess.run(
            [
                sys.executable,
                str(QUALITY_GATE / "verify_stage_sequence.py"),
                "--feature",
                str(feature),
                "--through",
                through,
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )

    def _baseline(self, feature, gate):
        return subprocess.run(
            [
                sys.executable,
                str(QUALITY_GATE / "approve_gate.py"),
                "--feature", str(feature), "--gate", str(gate), "--baseline",
            ],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )

    def test_approved_gate_without_hash_is_stale(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-01-gatehash"
            shutil.copytree(REPO_ROOT / "templates/feature-skeleton", feature)
            self._approved_feature(feature)

            result = self._gate_sequence(feature, "02")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("has no content hash recorded", result.stdout)

    def test_rederived_stage_invalidates_prior_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-01-gatehash"
            shutil.copytree(REPO_ROOT / "templates/feature-skeleton", feature)
            self._approved_feature(feature)
            for gate in (1, 2, 3):
                self.assertEqual(self._baseline(feature, gate).returncode, 0)
            # Baseline must now pass.
            self.assertEqual(self._gate_sequence(feature, "05").returncode, 0)

            # Re-derive a Gate 2 stage (02 concepts) — approval becomes stale.
            concept_out = Path(stages.stage_by_id("02").output_dir(str(feature)))
            (concept_out / "concept-changed.md").write_text("changed content")

            result = self._gate_sequence(feature, "05")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Gate 2", result.stdout)
            self.assertIn("stale", result.stdout)

    def test_baseline_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-01-gatehash"
            shutil.copytree(REPO_ROOT / "templates/feature-skeleton", feature)
            self._approved_feature(feature)
            first = self._baseline(feature, 1)
            second = self._baseline(feature, 1)
            self.assertEqual(first.returncode, 0)
            self.assertEqual(second.returncode, 0)
            self.assertIn("already current", second.stdout)


class ConceptStateRelationalTests(unittest.TestCase):
    """Stage 02 gate: concept state must be relational, not object fields."""

    def _run(self, concept_dir):
        return subprocess.run(
            [
                sys.executable,
                str(QUALITY_GATE / "verify_concept_state_relational.py"),
                "--concept-dir", str(concept_dir),
            ],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )

    def _write(self, concept_dir, name, state_body):
        (concept_dir / name).write_text(
            f"concept {name[:-len('.concept.md')]}\n"
            f"purpose\n    test concept\n\n## State\n\n```\n{state_body}\n```\n",
            encoding="utf-8",
        )

    def test_relational_state_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            d = Path(temporary)
            self._write(d, "User.concept.md",
                        "username: UserId -> String   -- mandatory\n")
            r = self._run(d)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_bare_field_list_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            d = Path(temporary)
            self._write(d, "User.concept.md", "userid\nusername\npassword\n")
            r = self._run(d)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("object-oriented trap", r.stdout)

    def test_self_referential_subject_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            d = Path(temporary)
            self._write(d, "Account.concept.md",
                        "username: Account -> String\n")
            r = self._run(d)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("concept's own name", r.stdout)

    def test_stateless_concept_is_exempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            d = Path(temporary)
            self._write(d, "Clock.concept.md", "*None.* Clock is stateless.\n")
            r = self._run(d)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
