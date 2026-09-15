#!/usr/bin/env python3
"""Fixture tests for verify_test_continuity.py (contract T2)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "quality-gate" / "verify_test_continuity.py"


def run(*args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd,
                          capture_output=True, text=True)


class TestContinuityTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.src = self.root / "app/src/test/java"
        pkg = self.src / "dev/example/concepts"
        pkg.mkdir(parents=True)
        self.test_file = pkg / "PasswordAuthVerifyTest.java"
        self.test_file.write_text("// red body\n", encoding="utf-8")

    def _map_with(self, body: str) -> Path:
        m = self.root / "concept-test-derivation.md"
        m.write_text(
            "# Derivation map\n\nsome prose\n\n"
            "## Test file continuity\n\n" + body,
            encoding="utf-8")
        return m

    def test_pass_when_files_unchanged(self):
        import hashlib
        digest = hashlib.sha256(self.test_file.read_bytes()).hexdigest()
        m = self._map_with(
            f"| `dev/example/concepts/PasswordAuthVerifyTest.java` | `{digest}` |\n")
        r = run("--derivation", str(m),
                "--test-source-root", str(self.src), cwd=self.root)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS  test continuity: 1 test file(s)", r.stdout)

    def test_fail_on_drift_lists_files_and_routing(self):
        m = self._map_with(
            "| `dev/example/concepts/PasswordAuthVerifyTest.java` | "
            f"`{'0' * 64}` |\n")
        r = run("--derivation", str(m),
                "--test-source-root", str(self.src), cwd=self.root)
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL  test continuity: 1 test file(s) changed", r.stdout)
        self.assertIn("drifted:", r.stdout)
        self.assertIn("R17 re-entry", r.stdout)
        self.assertIn("never edit red tests from the green stage", r.stdout)

    def test_skip_when_section_absent(self):
        m = self.root / "concept-test-derivation.md"
        m.write_text("# Derivation map\n\nno continuity section\n",
                     encoding="utf-8")
        r = run("--derivation", str(m),
                "--test-source-root", str(self.src), cwd=self.root)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("SKIP", r.stdout)

    def test_fail_when_listed_file_missing(self):
        m = self._map_with(
            "| `dev/example/concepts/NoSuchTest.java` | "
            f"`{'a' * 64}` |\n")
        r = run("--derivation", str(m),
                "--test-source-root", str(self.src), cwd=self.root)
        self.assertEqual(r.returncode, 1)
        self.assertIn("missing:", r.stdout)


if __name__ == "__main__":
    unittest.main()
