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


class StageWorkflowTests(unittest.TestCase):

    def test_fresh_skeleton_routes_through_each_red_green_stage(self):
        expected_stage_ids = [
            "01", "01a", "01b", "02", "03", "03a", "03b", "04a", "04b",
            "04c", "04d-red", "04d-green", "04e-red", "04e-green", "05",
        ]
        self.assertEqual([stage.id for stage in stages.STAGES], expected_stage_ids)

        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-01-workflow"
            shutil.copytree(REPO_ROOT / "templates/feature-skeleton", feature)
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


if __name__ == "__main__":
    unittest.main()