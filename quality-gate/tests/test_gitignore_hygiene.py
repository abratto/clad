#!/usr/bin/env python3
"""Guard: build/scratch artefacts stay out of version control.

`scratch/`, `references/`, `target/`, and the Python caches are local working
state (the `.gitignore` says so). Nothing stops a `git add -f` or a stray
`git add .` from committing them, which bloats the seed and leaks a developer's
local prototype. This check asserts each path is both ignored AND untracked.
"""

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

IGNORED_PATHS = (
    "scratch/probe.md",
    "references/Probe.java",
    "quality-gate/__pycache__/x.pyc",
    ".pytest_cache/README.md",
    "reference-impl/target/x.jar",
)


def _git(*args):
    return subprocess.run(["git", *args], cwd=REPO_ROOT,
                          capture_output=True, text=True)


class GitignoreHygieneTests(unittest.TestCase):

    def test_local_state_paths_are_ignored(self):
        for path in IGNORED_PATHS:
            result = _git("check-ignore", path)
            self.assertEqual(result.returncode, 0,
                             f"{path} is not ignored by .gitignore")

    def test_local_state_paths_are_untracked(self):
        for top in ("scratch", "references"):
            result = _git("ls-files", top)
            self.assertEqual(result.stdout.strip(), "",
                             f"tracked file under {top}/: {result.stdout}")
        caches = _git("ls-files", "*__pycache__*", "*.pyc", "*pytest_cache*",
                      "*/target/*")
        self.assertEqual(caches.stdout.strip(), "",
                         f"tracked build artefacts: {caches.stdout}")


if __name__ == "__main__":
    unittest.main()
