#!/usr/bin/env python3
"""Regression coverage for verify_mutation_score.py (R24, DR-0001)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"


def run(*args):
    return subprocess.run([sys.executable, *args], cwd=REPO_ROOT,
                          capture_output=True, text=True)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class MutationScoreTests(unittest.TestCase):

    def feature(self, temporary, *, command, threshold="80"):
        root = Path(temporary)
        feature = root / "features/UC-01-x"
        feature.mkdir(parents=True)
        props = f"mutation.threshold={threshold}\n"
        if command is not None:
            props += f"mutation.command={command}\n"
        write(root / "clad.properties", props)
        return feature

    def test_score_above_threshold_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary,
                                   command="echo 'MUTATION_SCORE: 91.5'")
            r = run(str(QG / "verify_mutation_score.py"),
                    "--feature-root", str(feature), "--scope", "concepts")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("91.5", r.stdout)

    def test_score_below_threshold_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary,
                                   command="echo 'MUTATION_SCORE: 42'")
            r = run(str(QG / "verify_mutation_score.py"),
                    "--feature-root", str(feature), "--scope", "concepts")
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("42.0%", r.stdout)

    def test_no_command_skips(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary, command=None)
            r = run(str(QG / "verify_mutation_score.py"),
                    "--feature-root", str(feature), "--scope", "concepts")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("SKIP", r.stdout)

    def test_missing_score_line_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary, command="echo 'no score here'")
            r = run(str(QG / "verify_mutation_score.py"),
                    "--feature-root", str(feature), "--scope", "concepts")
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("no", r.stdout.lower())

    def test_scope_specific_score_preferred(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(
                temporary,
                command="printf 'MUTATION_SCORE: 10\\nMUTATION_SCORE.syncs: 99\\n'")
            r = run(str(QG / "verify_mutation_score.py"),
                    "--feature-root", str(feature), "--scope", "syncs")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("99.0", r.stdout)

    def test_skip_without_require_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(
                temporary, command="echo 'MUTATION_SKIP: unsupported jvm'")
            r = run(str(QG / "verify_mutation_score.py"),
                    "--feature-root", str(feature), "--scope", "concepts")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("SKIP", r.stdout)

    def test_skip_with_require_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(
                temporary, command="echo 'MUTATION_SKIP: unsupported jvm'")
            r = run(str(QG / "verify_mutation_score.py"),
                    "--feature-root", str(feature), "--scope", "concepts",
                    "--require")
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("required", r.stdout.lower())

    def test_no_command_with_require_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary, command=None)
            r = run(str(QG / "verify_mutation_score.py"),
                    "--feature-root", str(feature), "--scope", "concepts",
                    "--require")
            self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
