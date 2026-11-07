#!/usr/bin/env python3
"""Regression coverage for verify_release_profile.py (proposal 3).

A repo that declares `release.enforce=true` must run mutation (require=true) and,
for a persistent profile, record durable proof. The template (`false`) skips.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "quality-gate" / "verify_release_profile.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          cwd=REPO_ROOT, capture_output=True, text=True)


def repo(tmp, **props):
    root = Path(tmp)
    defaults = {"release.enforce": "false", "mutation.command": "",
                "mutation.require": "false", "storage.persistent": "false"}
    defaults.update(props)
    (root / "clad.properties").write_text(
        "".join(f"{k}={v}\n" for k, v in defaults.items()), encoding="utf-8")
    return str(root)


class ReleaseProfileTests(unittest.TestCase):

    def test_template_skips(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run("--repo-root", repo(tmp))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("SKIP", r.stdout)

    def test_require_on_a_template_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run("--repo-root", repo(tmp), "--require")
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("release.enforce=true", r.stdout)

    def test_consistent_release_profile_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, **{"release.enforce": "true",
                                "mutation.command": "scripts/mutation-score.sh",
                                "mutation.require": "true"})
            r = run("--repo-root", root)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("PASS", r.stdout)

    def test_release_without_mutation_require_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, **{"release.enforce": "true",
                                "mutation.command": "scripts/mutation-score.sh",
                                "mutation.require": "false"})
            r = run("--repo-root", root)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("mutation.require must be true", r.stdout)

    def test_persistent_release_without_durable_proof_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, **{"release.enforce": "true",
                                "mutation.command": "x",
                                "mutation.require": "true",
                                "storage.persistent": "true"})
            feature = Path(tmp) / "features" / "UC-01-x"
            (feature / "stages" / "05_verify" / "output").mkdir(parents=True)
            r = run("--repo-root", root, "--feature-root", str(feature))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("durable proof", r.stdout)


if __name__ == "__main__":
    unittest.main()
