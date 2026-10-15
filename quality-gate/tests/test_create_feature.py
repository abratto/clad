#!/usr/bin/env python3
"""Regression coverage for create_feature.py (D7: bootstrap a feature)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
SKELETON = REPO_ROOT / "templates" / "feature-skeleton"


def run(*args):
    return subprocess.run(
        [sys.executable, str(QG / "create_feature.py"), *args],
        cwd=REPO_ROOT, capture_output=True, text=True)


class CreateFeatureTests(unittest.TestCase):

    def _repo(self, tmp):
        repo = Path(tmp)
        (repo / "clad.properties").write_text(
            "concept.impl.dir=reference-impl/java-legible/src/main/java/"
            "dev/legible/example/login\n"
            "test.source.root=reference-impl/java-legible/src/test/java\n",
            encoding="utf-8")
        return repo

    def test_bootstraps_and_fills_the_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            result = run("--slug", "UC-99-x", "--repo-root", str(repo),
                         "--skeleton", str(SKELETON))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            layout = (repo / "features/UC-99-x/_config/package-and-layout.md")
            self.assertTrue(layout.is_file())
            text = layout.read_text(encoding="utf-8")
            self.assertIn("dev.legible.example.login", text)
            self.assertNotIn("`TBD`", text)

    def test_refuses_an_existing_feature(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            run("--slug", "UC-99-x", "--repo-root", str(repo),
                "--skeleton", str(SKELETON))
            again = run("--slug", "UC-99-x", "--repo-root", str(repo),
                        "--skeleton", str(SKELETON))
            self.assertNotEqual(again.returncode, 0)
            self.assertIn("already exists", again.stdout)


if __name__ == "__main__":
    unittest.main()
