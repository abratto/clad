#!/usr/bin/env python3
"""Regression coverage for verify_concept_novelty.py and
lint_concept_overlap.py (maintenance change `concept-novelty-gate`).

A NEW responsibility-map row whose name + action tokens overlap an existing
concepts-catalog row must justify the non-fit in the map's
`## Why not existing` section. The linter surfaces the same overlaps
advisoriily (exit 0 always).
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"

CATALOG = """# Concepts catalog

| Concept | Purpose | Type params | Actions | Introduced by | Used by | Notes |
|---|---|---|---|---|---|---|
| `Session` | to maintain a session for a verified user | `UserId` | `grant`, `lookup`, `revoke` | UC-00-login | UC-00-login | — |
"""

RESP_MAP_COLLIDING = """# Responsibility map — UC-01-a

## Concepts

| Concept | Origin | Owned state (one line) | Owned actions | Notes |
|---|---|---|---|---|
| `Web` | `new` | route table | `request`, `respond` | bootstrap |
| `SessionReplay` | `new` | `grants: Map<UserId, Grant>` | `grant`, `lookup` | x |
"""

WHY_NOT = """
## Why not existing

- `Session` — this feature replays historical grants; `Session` owns live
  sessions only.
"""

RESP_MAP_NOVEL = """# Responsibility map — UC-01-a

## Concepts

| Concept | Origin | Owned state (one line) | Owned actions | Notes |
|---|---|---|---|---|
| `Web` | `new` | route table | `request`, `respond` | bootstrap |
| `Upvoting` | `new` | `votes: UserId -> PostId` | `upvote`, `unvote` | x |
"""

RESP_MAP_NO_ORIGIN = """# Responsibility map — UC-01-a

## Concepts

| Concept | Owned state (one line) | Owned actions | Notes |
|---|---|---|---|
| `Upvoting` | `votes: UserId -> PostId` | `upvote`, `unvote` | x |
"""


def run(script, *args):
    return subprocess.run(
        [sys.executable, str(QG / script), *args],
        cwd=REPO_ROOT, capture_output=True, text=True)


class ConceptNoveltyTests(unittest.TestCase):

    def _feature(self, root, resp_text, with_catalog=True):
        root = Path(root)
        feature = root / "features" / "UC-01-a"
        out = feature / "stages/01a_responsibility-map/output"
        out.mkdir(parents=True)
        (out / "responsibility-map.md").write_text(resp_text,
                                                   encoding="utf-8")
        if with_catalog:
            system = root / "features" / "_system"
            system.mkdir(parents=True)
            (system / "concepts-catalog.md").write_text(CATALOG,
                                                        encoding="utf-8")
        return str(feature)

    def test_collision_without_justification_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(temporary, RESP_MAP_COLLIDING)
            result = run("verify_concept_novelty.py", "--feature", feature)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SessionReplay", result.stdout)
            self.assertIn("Session", result.stdout)
            self.assertIn("Why not existing", result.stdout)

    def test_collision_with_justification_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(
                temporary, RESP_MAP_COLLIDING + WHY_NOT)
            result = run("verify_concept_novelty.py", "--feature", feature)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)

    def test_genuinely_novel_concept_needs_no_section(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(temporary, RESP_MAP_NOVEL)
            result = run("verify_concept_novelty.py", "--feature", feature)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)

    def test_missing_catalog_skips(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(temporary, RESP_MAP_COLLIDING,
                                    with_catalog=False)
            result = run("verify_concept_novelty.py", "--feature", feature)
            self.assertEqual(result.returncode, 0)
            self.assertIn("SKIP", result.stdout)

    def test_no_origin_column_skips(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(temporary, RESP_MAP_NO_ORIGIN)
            result = run("verify_concept_novelty.py", "--feature", feature)
            self.assertEqual(result.returncode, 0)
            self.assertIn("SKIP", result.stdout)

    def test_linter_warns_but_exits_zero(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(temporary, RESP_MAP_COLLIDING)
            result = run("lint_concept_overlap.py", "--feature", feature)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)
            self.assertIn("WARN", result.stdout)
            self.assertIn("SessionReplay", result.stdout)

    def test_linter_clean_when_no_overlap(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(temporary, RESP_MAP_NOVEL)
            result = run("lint_concept_overlap.py", "--feature", feature)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)
            self.assertIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
