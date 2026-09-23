#!/usr/bin/env python3
"""Regression coverage for verify_code_refs.py (advisory).

A backticked `path/File.java` must resolve, and `File.java:LINE` must be within
the file. The check never blocks (exit 0)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"


def run(*args):
    return subprocess.run(
        [sys.executable, str(QG / "verify_code_refs.py"), *args],
        cwd=REPO_ROOT, capture_output=True, text=True)


class CodeRefTests(unittest.TestCase):

    def test_unresolved_path_warns_but_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs/a.md").write_text(
                "see `src/gone/Missing.java`", encoding="utf-8")
            result = run("--root", str(root), "--dirs", "docs")
            self.assertEqual(result.returncode, 0, "advisory must not block")
            self.assertIn("WARN", result.stdout)

    def test_line_past_eof_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "src").mkdir()
            (root / "src/Foo.java").write_text("one\ntwo\n", encoding="utf-8")
            (root / "docs/a.md").write_text(
                "see `src/Foo.java:99`", encoding="utf-8")
            result = run("--root", str(root), "--dirs", "docs")
            self.assertEqual(result.returncode, 0, "advisory must not block")
            self.assertIn("past the end", result.stdout)

    def test_resolving_reference_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "src").mkdir()
            (root / "src/Foo.java").write_text("one\ntwo\n", encoding="utf-8")
            (root / "docs/a.md").write_text(
                "see `src/Foo.java:2`", encoding="utf-8")
            result = run("--root", str(root), "--dirs", "docs")
            self.assertEqual(result.returncode, 0)
            self.assertIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
