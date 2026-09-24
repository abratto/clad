#!/usr/bin/env python3
"""Keep quality-gate/INDEX.md current (maintenance/gate-index.md).

INDEX.md is generated from the machine map (clad_stages.py + the project-level
calls); this test asserts regenerating it produces no diff, so the hand-written
catalogs cannot drift from the real gate surface again.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
REPO_INDEX = QG / "INDEX.md"
SKILL = REPO_ROOT / "skills" / "clad-quality-gate" / "SKILL.md"


class GateIndexTests(unittest.TestCase):

    def test_index_is_current(self):
        result = subprocess.run(
            [sys.executable, str(QG / "generate_gate_index.py"), "--check"],
            cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_index_regeneration_is_deterministic(self):
        # Regenerate into a temp copy and compare to the committed file.
        self.assertTrue(REPO_INDEX.is_file(), "quality-gate/INDEX.md is missing")
        committed = REPO_INDEX.read_text(encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(QG / "generate_gate_index.py")],
            cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(REPO_INDEX.read_text(encoding="utf-8"), committed,
                         "INDEX.md regeneration changed the file — it was stale")

    def test_every_wired_script_is_listed(self):
        sys.path.insert(0, str(QG))
        import clad_stages as cs  # noqa: E402
        index = REPO_INDEX.read_text(encoding="utf-8")
        wired = {c.script for s in cs.STAGES for c in s.checks}
        wired |= {"verify_artefacts.py", "verify_stage_sequence.py",
                  "verify_maintenance_change_readiness.py",
                  "verify_iterative_change_coupling.py"}
        missing = sorted(script for script in wired
                         if f"`{script}`" not in index)
        self.assertEqual(missing, [], f"INDEX.md does not list: {missing}")

    def test_skill_points_at_the_sources_not_an_enumeration(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("INDEX.md", text,
                      "the skill must point at the generated index")
        self.assertIn("verify_artefacts.py", text)
        # It must no longer enumerate a partial script table.
        self.assertNotIn("| Script | Checks |", text,
                         "the skill should not restate a partial script table")


if __name__ == "__main__":
    unittest.main()
