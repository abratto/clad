#!/usr/bin/env python3
"""Regression coverage for the `./clad` CLI active-feature discovery.

The wrapper auto-discovers the feature from `features/*/RESUME.md`. A
freshly-created (unstarted, `Current stage: TBD`) feature must not outrank
one that is actually in progress, and a `feature complete` feature must
never be chosen over a live one.
"""

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

    def _run(self, cwd, *args):
        return subprocess.run(
            ["bash", str(CLAD), *args],
            cwd=cwd, capture_output=True, text=True,
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


if __name__ == "__main__":
    unittest.main()
