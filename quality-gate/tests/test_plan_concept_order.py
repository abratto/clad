#!/usr/bin/env python3
"""Regression coverage for check_plan_concept_order.py (maintenance change
`plan-concept-order-check`). Advisory only — every outcome exits 0; the
tests assert on WARN/PASS content."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "quality-gate" / "check_plan_concept_order.py"

BOARD = """# Plan board

## Feature queue

| Feature | Status | Priority | Depends on | Next gate | Notes |
|---|---|---:|---|---|---|
{rows}
"""

RESP_MAP = """# Responsibility map — {slug}

## Concepts

| Concept | Origin | Owned state (one line) | Owned actions | Notes |
|---|---|---|---|---|
{rows}
"""


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          cwd=REPO_ROOT, capture_output=True, text=True)


def make_world(tmp, board_rows, maps):
    root = Path(tmp)
    (root / "plan-board.md").write_text(BOARD.format(rows=board_rows),
                                        encoding="utf-8")
    features = root / "features"
    for slug, rows in maps.items():
        out = (features / slug / "stages" / "01a_responsibility-map"
               / "output")
        out.mkdir(parents=True)
        (out / "responsibility-map.md").write_text(
            RESP_MAP.format(slug=slug, rows=rows), encoding="utf-8")
    return str(root / "plan-board.md"), str(features)


class PlanConceptOrderTests(unittest.TestCase):

    def test_missing_board_skips(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run("--plan-board", str(Path(tmp) / "absent.md"),
                         "--features-dir", str(Path(tmp) / "features"))
            self.assertEqual(result.returncode, 0)
            self.assertIn("SKIP", result.stdout)

    def test_extension_before_introduction_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            board, features = make_world(
                tmp,
                "| UC-02-b | next | 1 | none | | |\n"
                "| UC-03-c | later | 2 | none | | |",
                {"UC-02-b": "| `Session` | `extends:UC-03-c` | `t` | `grant` | |",
                 "UC-03-c": "| `Session` | `new` | `t` | `grant` | |"})
            result = run("--plan-board", board, "--features-dir", features)
            self.assertEqual(result.returncode, 0)
            self.assertIn("WARN", result.stdout)
            self.assertIn("UC-03-c", result.stdout)
            self.assertIn("LATER", result.stdout)

    def test_introducer_absent_from_board_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            board, features = make_world(
                tmp,
                "| UC-02-b | next | 1 | none | | |",
                {"UC-02-b": "| `Session` | `extends:UC-09-zz` | `t` | `grant` | |"})
            result = run("--plan-board", board, "--features-dir", features)
            self.assertEqual(result.returncode, 0)
            self.assertIn("not on the plan board", result.stdout)

    def test_duplicate_new_in_same_wave_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            board, features = make_world(
                tmp,
                "| UC-02-b | doing | 1 | none | | |\n"
                "| UC-03-c | next | 2 | none | | |",
                {"UC-02-b": "| `Upvoting` | `new` | `v` | `upvote` | |",
                 "UC-03-c": "| `Upvoting` | `new` | `v` | `upvote` | |"})
            result = run("--plan-board", board, "--features-dir", features)
            self.assertEqual(result.returncode, 0)
            self.assertIn("guaranteed Gate-2 collision", result.stdout)

    def test_clean_board_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            board, features = make_world(
                tmp,
                "| UC-02-b | done | 1 | none | | |\n"
                "| UC-03-c | next | 2 | none | | |",
                {"UC-02-b": "| `Session` | `new` | `t` | `grant` | |",
                 "UC-03-c": "| `Session` | `extends:UC-02-b` | `t` | `grant` | |"})
            result = run("--plan-board", board, "--features-dir", features)
            self.assertEqual(result.returncode, 0)
            self.assertIn("PASS", result.stdout)
            self.assertNotIn("WARN", result.stdout)


if __name__ == "__main__":
    unittest.main()
