#!/usr/bin/env python3
"""Regression coverage for verify_durable_proof.py (finding 19).

A profile that declares `storage.persistent=true` must record a passing durable
(Postgres) run at Stage-05 close, because the durable lane is Docker-gated and
outside `test.command` — otherwise a Postgres-only defect lets the feature close
green. A non-persistent profile skips.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
SCRIPT = QG / "verify_durable_proof.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          cwd=REPO_ROOT, capture_output=True, text=True)


def world(tmp, persistent, durable_text=None):
    root = Path(tmp)
    (root / "clad.properties").write_text(
        f"storage.persistent={persistent}\n", encoding="utf-8")
    feature = root / "features" / "UC-01-x"
    out = feature / "stages" / "05_verify" / "output"
    out.mkdir(parents=True)
    if durable_text is not None:
        (out / "durable-proof.md").write_text(durable_text, encoding="utf-8")
    return str(feature)


PASS_PROOF = (
    "# Durable proof\n\n"
    "- **Command:** `mvn -f apps/x/pom.xml test -Dclad.postgres=true`\n"
    "- **Result:** `PASS`\n"
)


class DurableProofTests(unittest.TestCase):

    def test_non_persistent_skips(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = world(tmp, "false")
            r = run("--feature", feature)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("SKIP", r.stdout)

    def test_persistent_without_proof_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = world(tmp, "true")
            r = run("--feature", feature)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("without durable proof", r.stdout)

    def test_persistent_with_passing_proof_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = world(tmp, "true", PASS_PROOF)
            r = run("--feature", feature)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("PASS", r.stdout)

    def test_proof_without_a_durable_command_fails(self):
        bad = ("# Durable proof\n\n- **Command:** `mvn test`\n"
               "- **Result:** `PASS`\n")
        with tempfile.TemporaryDirectory() as tmp:
            feature = world(tmp, "true", bad)
            r = run("--feature", feature)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("durable invocation", r.stdout)

    def test_proof_not_passing_fails(self):
        bad = ("# Durable proof\n\n"
               "- **Command:** `mvn test -Dclad.postgres=true`\n"
               "- **Result:** `FAIL`\n")
        with tempfile.TemporaryDirectory() as tmp:
            feature = world(tmp, "true", bad)
            r = run("--feature", feature)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("must be `PASS`", r.stdout)


if __name__ == "__main__":
    unittest.main()
