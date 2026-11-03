#!/usr/bin/env python3
"""Tests for verify_changelog_claims.py."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"


def run(*args):
    return subprocess.run([sys.executable, str(QG / "verify_changelog_claims.py"),
                           *map(str, args)], cwd=REPO_ROOT,
                          capture_output=True, text=True)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class ChangelogClaimTests(unittest.TestCase):

    def _repo(self, root, changelog_body, make_paths=()):
        for rel in make_paths:
            write(root / rel, "x\n")
        write(root / "CHANGELOG.md", changelog_body)

    def test_cited_file_must_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root, "# Changelog\n\n## [0.1.0] — 2026-01-01\n\n"
                             "- Moves to `quality-gate/missing.py`.\n")
            r = run("--root", root)
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("missing.py", r.stdout)

    def test_existing_file_passes_without_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root, "# Changelog\n\n## [0.1.0] — 2026-01-01\n\n"
                             "- Moves to `quality-gate/present.py`.\n",
                       make_paths=["quality-gate/present.py"])
            r = run("--root", root)
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertIn("PASS", r.stdout)

    def test_directory_mentions_are_not_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root, "# Changelog\n\n## [0.1.0] — 2026-01-01\n\n"
                             "- Searches `_generated/rmap-baselines/`.\n")
            r = run("--root", root)
            self.assertEqual(r.returncode, 0, r.stdout)

    def test_version_tag_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root, "# Changelog\n\n## [0.2.0] — 2026-01-01\n\n- x\n")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.email=a@b", "-c", "user.name=a",
                            "commit", "-qm", "x"], cwd=root, check=True)
            subprocess.run(["git", "tag", "v0.1.0"], cwd=root, check=True)
            r = run("--root", root)
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("v0.1.0", r.stdout)


if __name__ == "__main__":
    unittest.main()
