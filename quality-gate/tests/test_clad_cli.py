#!/usr/bin/env python3
"""Regression coverage for the `./clad` CLI active-feature discovery.

The wrapper auto-discovers the feature from `features/*/RESUME.md`. A
freshly-created (unstarted, `Current stage: TBD`) feature must not outrank
one that is actually in progress, and a `feature complete` feature must
never be chosen over a live one.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLAD = REPO_ROOT / "clad"


def _resume(stage_line: str, complete: bool = False) -> str:
    tail = ("- **Next stage:** `None — feature complete`\n"
            if complete else "")
    return f"# RESUME\n\n- **Current stage:** `{stage_line}`\n{tail}"


class CladCliDiscoveryTests(unittest.TestCase):

    def _feature(self, features, name, body):
        d = features / name
        (d / "stages").mkdir(parents=True, exist_ok=True)
        (d / "RESUME.md").write_text(body, encoding="utf-8")

    def _changes(self, features, name, filenames):
        d = features / name / "_changes"
        d.mkdir(parents=True, exist_ok=True)
        for filename in filenames:
            (d / filename).write_text("- **Status:** `active`\n", encoding="utf-8")

    def _git_init(self, root):
        for args in (["init", "-q"], ["config", "user.email", "t@e.st"],
                     ["config", "user.name", "t"], ["add", "-A"]):
            subprocess.run(["git", *args], cwd=root, check=True,
                           capture_output=True, text=True)

    def _run(self, cwd, *args, env=None):
        return subprocess.run(
            ["bash", str(CLAD), *args],
            cwd=cwd, capture_output=True, text=True,
            env={**os.environ, **(env or {})},
        )

    def test_in_progress_feature_beats_unstarted_and_complete(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features = root / "features"
            self._feature(features, "UC-00-complete",
                          _resume("None — feature complete", complete=True))
            self._feature(features, "UC-01-active",
                          _resume("Stage 02 — Concept specs"))
            self._feature(features, "UC-02-fresh", _resume("TBD"))

            result = self._run(root, "feature")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout.strip(), "UC-01-active")

    def test_fresh_feature_chosen_when_none_in_progress(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features = root / "features"
            self._feature(features, "UC-00-complete",
                          _resume("None — feature complete", complete=True))
            self._feature(features, "UC-02-fresh", _resume("TBD"))

            result = self._run(root, "feature")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout.strip(), "UC-02-fresh")


    def test_complete_feature_with_uncommitted_changes_never_outranks(self):
        """A completed feature (e.g. a re-synced worked example) carrying
        uncommitted _changes/ is not itself in progress, so it must not be
        picked over a live feature — the exact mis-target that approved the
        wrong feature's gate."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features = root / "features"
            self._feature(features, "UC-00-worked-example",
                          _resume("None — feature complete", complete=True))
            self._feature(features, "UC-01-active", _resume("Stage 03 — Syncs"))
            self._changes(features, "UC-00-worked-example", ["re-synced.md"])
            self._git_init(root)

            result = self._run(root, "feature")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout.strip(), "UC-01-active")

    def test_two_in_progress_with_uncommitted_changes_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features = root / "features"
            self._feature(features, "UC-01-a", _resume("Stage 03 — Syncs"))
            self._feature(features, "UC-02-b", _resume("Stage 02 — Concept specs"))
            self._changes(features, "UC-01-a", ["change.md"])
            self._changes(features, "UC-02-b", ["change.md"])
            self._git_init(root)

            result = self._run(root, "feature")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Ambiguous", result.stderr)
            self.assertIn("CLAD_FEATURE", result.stderr)

    def test_clad_feature_override_wins(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features = root / "features"
            self._feature(features, "UC-01-a", _resume("Stage 03 — Syncs"))
            self._feature(features, "UC-02-b", _resume("Stage 02 — Concept specs"))

            result = self._run(root, "feature", env={"CLAD_FEATURE": "UC-02-b"})
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout.strip(), "UC-02-b")


if __name__ == "__main__":
    unittest.main()
