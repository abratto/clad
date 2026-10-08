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
import verify_stage_sequence  # noqa: E402


class StageWorkflowTests(unittest.TestCase):

    def make_feature(self, temporary):
        feature = Path(temporary) / "UC-01-workflow"
        shutil.copytree(REPO_ROOT / "templates/feature-skeleton", feature)
        # A configured feature: `_config/package-and-layout.md` must be filled
        # by Stage 04 (the skeleton ships `TBD`; verify_profile_paths fails a
        # still-TBD layout once the feature reaches 04a).
        (feature / "_config" / "package-and-layout.md").write_text(
            "# Package & layout\n\n"
            "- **APP_PACKAGE_ROOT:** `dev.legible.example`\n"
            "- **APP_SOURCE_ROOT:** `reference-impl/java-legible/src/main/java`\n"
            "- **APP_TEST_SOURCE_ROOT:** `reference-impl/java-legible/src/test/java`\n",
            encoding="utf-8")
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

    def test_no_output_03b_is_noop_once_concepts_are_authored(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.make_feature(temporary)
            # A fresh skeleton has not authored concepts yet → 03b is NOT a
            # no-op, so routing must still pass through it normally.
            self.assertFalse(stages.stage_is_noop(str(feature), "03b"))
            # Once the concept set is authored (02 emits concept-bindings.md)
            # and no concept owns state, 03b is satisfied without an output dir.
            bindings = Path(stages.stage_by_id("02").output_dir(str(feature)))
            bindings.mkdir(parents=True, exist_ok=True)
            (bindings / "concept-bindings.md").write_text(
                "# bindings", encoding="utf-8")
            self.assertTrue(stages.stage_is_noop(str(feature), "03b"))
            # With its predecessor satisfied, the no-op 03b has evidence.
            three_a = Path(stages.stage_by_id("03a").output_dir(str(feature)))
            three_a.mkdir(parents=True, exist_ok=True)
            (three_a / "evidence.md").write_text("03a", encoding="utf-8")
            self.assertTrue(
                verify_stage_sequence.stage_has_evidence(str(feature), "03b"))

    def test_no_output_03b_is_not_noop_when_a_concept_owns_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.make_feature(temporary)
            # Bindings authored (the gate's second condition holds)...
            bindings = Path(stages.stage_by_id("02").output_dir(str(feature)))
            bindings.mkdir(parents=True, exist_ok=True)
            (bindings / "concept-bindings.md").write_text(
                "# bindings", encoding="utf-8")
            # ...but a NEW concept owns state, so 03b must produce a model.
            resp = Path(stages.stage_by_id("01a").output_dir(str(feature)))
            resp.mkdir(parents=True, exist_ok=True)
            (resp / "responsibility-map.md").write_text(
                "# Responsibility map\n\n## Concepts\n\n"
                "| Concept | Origin | Owned state (one line) | Owned actions | Notes |\n"
                "|---|---|---|---|---|\n"
                "| `Thing` | `new` | `x: ThingId -> X` | `act` | |\n",
                encoding="utf-8")
            self.assertFalse(stages.stage_is_noop(str(feature), "03b"),
                             "a state-owning concept means 03b is not a no-op")

    def test_read_only_feature_advances_through_noop_03b_to_04a(self):
        # The reported bug: a read-only feature has a no-op 03b (no output dir)
        # but a populated 04a; the sequence guard must accept it through 04a
        # (it FAILED before the no-op mechanism).
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.make_feature(temporary)
            resume = feature / "RESUME.md"
            resume.write_text(
                resume.read_text(encoding="utf-8").replace("`pending`", "`approved`"),
                encoding="utf-8")
            for sid in ("01", "01a", "01b", "02", "03", "03a", "04a"):
                out = Path(stages.stage_by_id(sid).output_dir(str(feature)))
                out.mkdir(parents=True, exist_ok=True)
                (out / "evidence.md").write_text(sid, encoding="utf-8")
            # Author the concept set so 03b is a legitimate no-op.
            (Path(stages.stage_by_id("02").output_dir(str(feature)))
             / "concept-bindings.md").write_text("# bindings", encoding="utf-8")
            self.assertTrue(stages.stage_is_noop(str(feature), "03b"))
            result = self.sequence_result(feature, "04a")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_fresh_skeleton_routes_through_each_stage(self):
        expected_stage_ids = [
            "01", "01a", "01b", "02", "03", "03a", "03b", "04a", "04b",
            "04c", "04d", "04e", "05",
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

            # Routing: the stage model routes 04d -> 04e deterministically.
            self.assertEqual(advance.determine_stage(str(feature), "04d").id, "04d")
            next_stage = stages.next_stage("04d")
            self.assertIsNotNone(next_stage)
            self.assertEqual(next_stage.id, "04e")
            self.assertEqual(
                next_stage.context_path(str(feature)),
                str(feature / "stages/04_implement/04e_sync-impl/CONTEXT.md"))

    def test_new_partial_stage_history_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.make_feature(temporary)
            self.populate_through(feature, "04c")
            sync_out = Path(stages.stage_by_id("04e").output_dir(str(feature)))
            sync_out.mkdir(parents=True, exist_ok=True)
            (sync_out / "implementation.md").write_text("skipped 04d")

            result = self.sequence_result(feature, "04e")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("04d", result.stdout)

    def test_legacy_red_green_tree_is_rejected(self):
        """Pre-DR-0001 red/green child trees are rejected, not migrated."""
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.make_feature(temporary)
            self.populate_through(feature, "04c")
            legacy = feature / (
                "stages/04_implement/04d_concept-tdd/04d_red-tests/output")
            legacy.mkdir(parents=True, exist_ok=True)
            (legacy / "concept-test-derivation.md").write_text("legacy red")
            sync_out = Path(stages.stage_by_id("04e").output_dir(str(feature)))
            sync_out.mkdir(parents=True, exist_ok=True)
            (sync_out / "implementation.md").write_text("new work")

            result = self.sequence_result(feature, "04e")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("04d", result.stdout)

    def test_legacy_stage_ids_are_gone(self):
        for legacy in ("04d-red", "04d-green", "04e-red", "04e-green"):
            self.assertIsNone(stages.stage_by_id(legacy), legacy)
        for current in ("04c", "04d", "04e"):
            self.assertIsNotNone(stages.stage_by_id(current), current)

    def test_active_reentry_uses_current_stage_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.make_feature(temporary)
            self.populate_through(feature, "04c")
            changes = feature / "_changes"
            changes.mkdir(exist_ok=True)
            (changes / "concept-correction.md").write_text(
                "- **Status:** `active`\n"
                "- **Change category:** `structural`\n"
                "- **Earliest re-entry stage:** `04d`\n"
                "- **Why:** correct the concept test derivation\n",
                encoding="utf-8",
            )
            reentry = Path(stages.stage_by_id("04d").output_dir(str(feature)))
            reentry.mkdir(parents=True, exist_ok=True)
            (reentry / "verification-evidence.md").write_text("re-entry")

            result = self.sequence_result(feature, "04d")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


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


class GateApprovalAutonomyTests(unittest.TestCase):
    """auto-approved gates and stage pre-conditions must interoperate."""

    def _populate_all(self, feature):
        for stage in stages.STAGES:
            output = Path(stage.output_dir(str(feature)))
            output.mkdir(parents=True, exist_ok=True)
            (output / "evidence.md").write_text(stage.id, encoding="utf-8")

    def _sequence(self, feature, through):
        """The stage-order + gate-approval guard (absorbed the old
        verify_gate_approval.py)."""
        return subprocess.run(
            [
                sys.executable,
                str(QUALITY_GATE / "verify_stage_sequence.py"),
                "--feature", str(feature), "--through", through,
            ],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )

    def test_set_gate_status_warns_when_no_gate_line_matches(self):
        """A malformed RESUME must surface, not silently fail to record a gate
        (maintenance/gate-verdict-hardening.md)."""
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-01-warn"
            feature.mkdir()
            (feature / "RESUME.md").write_text(
                "# RESUME\n\n- **Feature:** `x`\n", encoding="utf-8")
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                wrote = advance.set_gate_status(str(feature), 2, "approved")
            self.assertFalse(wrote)
            out = captured.getvalue()
            self.assertIn("WARN", out)
            self.assertIn("Gate 2", out)
            self.assertIn("Architecture", out)

    def test_set_gate_status_warns_when_resume_missing(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-01-nofile"
            feature.mkdir()
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                wrote = advance.set_gate_status(str(feature), 1, "approved")
            self.assertFalse(wrote)
            self.assertIn("WARN", captured.getvalue())

    def test_set_gate_status_writes_a_matched_line(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-01-ok"
            feature.mkdir()
            (feature / "RESUME.md").write_text(
                "- **Gate 2 (Architecture):** `pending`\n", encoding="utf-8")
            wrote = advance.set_gate_status(str(feature), 2, "approved")
            self.assertTrue(wrote)
            self.assertIn("`approved`",
                          (feature / "RESUME.md").read_text(encoding="utf-8"))

    def test_auto_approved_gate_satisfies_stage_precondition(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-01-auto"
            shutil.copytree(REPO_ROOT / "templates/feature-skeleton", feature)
            resume = feature / "RESUME.md"
            resume.write_text(
                resume.read_text(encoding="utf-8").replace(
                    "`pending`", "`auto-approved`"),
                encoding="utf-8",
            )
            self._populate_all(feature)

            result = self._sequence(feature, "04c")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("auto-approved",
                          (feature / "RESUME.md").read_text(encoding="utf-8"))

    def test_autonomous_advance_records_auto_approved_and_unblocks_precondition(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-01-autonomous"
            shutil.copytree(REPO_ROOT / "templates/feature-skeleton", feature)
            usecase = Path(stages.stage_by_id("01").output_dir(str(feature)))
            usecase.mkdir(parents=True, exist_ok=True)
            (usecase / "usecase.md").write_text(
                "### Scenario: Login\n\nmain flow\n", encoding="utf-8")
            resp = Path(stages.stage_by_id("01a").output_dir(str(feature)))
            resp.mkdir(parents=True, exist_ok=True)
            (resp / "responsibility-map.md").write_text(
                "| Concept | State | Actions |\n|---|---|---|\n"
                "| Web | none | handle |\n",
                encoding="utf-8")
            output = Path(stages.stage_by_id("01b").output_dir(str(feature)))
            output.mkdir(parents=True, exist_ok=True)
            # Filename must match the Stage 01 scenario slug (`Login` -> login).
            (output / "login-chain.md").write_text(
                "| When | Then | Inputs | Outcome | Why |\n"
                "|---|---|---|---|---|\n"
                "| `Web.request[Routed]` | `Web.handle` | `routed` | `Ok` | entry |\n"
                "\n```mermaid\nstateDiagram-v2\n"
                "    [*] --> Web_request\n    Web_request --> [*]\n```\n",
                encoding="utf-8",
            )

            advance_result = subprocess.run(
                [
                    sys.executable,
                    str(QUALITY_GATE / "advance.py"),
                    "--feature", str(feature),
                    "--autonomous", "true",
                ],
                cwd=REPO_ROOT, capture_output=True, text=True,
            )
            self.assertEqual(advance_result.returncode, 0,
                             advance_result.stdout + advance_result.stderr)
            self.assertIn("auto-approved", (feature / "RESUME.md").read_text(
                encoding="utf-8"))

            precondition = self._sequence(feature, "01b")
            self.assertEqual(precondition.returncode, 0,
                             precondition.stdout + precondition.stderr)


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
