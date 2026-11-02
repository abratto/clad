#!/usr/bin/env python3
"""Regression: an empty Stage 03b output is not a data-model set.

A freshly bootstrapped feature carries the skeleton's `03b_data-model/output/`
with only `.gitkeep`. The project-level model-current check must skip it until
the stage actually authors models, otherwise every new UC fails before 03b.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"


def run(*args):
    return subprocess.run([sys.executable, str(QG / "verify_model_current.py"),
                           *map(str, args)],
                          cwd=REPO_ROOT, capture_output=True, text=True)


class ModelCurrentTests(unittest.TestCase):

    def test_empty_skeleton_feature_is_skipped(self):
        with tempfile.TemporaryDirectory() as temporary:
            features = Path(temporary) / "features"
            output = features / "UC-01-x/stages/03b-data-model/output"
            output.mkdir(parents=True)
            (output / ".gitkeep").write_text("", encoding="utf-8")
            (features / "UC-01-x/stages/02_concepts/output").mkdir(
                parents=True)
            result = run("--features-dir", features)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SKIP", result.stdout)

    def test_existing_features_with_models_are_still_checked(self):
        result = run("--features-dir", REPO_ROOT / "examples",
                     "--include-examples")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS  UC-00-login", result.stdout)


if __name__ == "__main__":
    unittest.main()
