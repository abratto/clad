#!/usr/bin/env python3
"""Regression coverage for verify_concept_bindings.py.

`concept-bindings.md` must agree with the 01a responsibility map (concept +
origin) and its actions must resolve against the concept's spec — the catalog's
"Used by" column derives from this file.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"


def run(*args):
    return subprocess.run(
        [sys.executable, str(QG / "verify_concept_bindings.py"), *args],
        cwd=REPO_ROOT, capture_output=True, text=True)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


RESP_MAP = """# Responsibility map

## Concepts

| Concept | Origin | Owned state (one line) | Owned actions | Notes |
|---|---|---|---|---|
| `Profiling` | `extends:UC-03-update-profile` | `f: Id -> T` | `readProfile` | — |
"""


def bindings(rows):
    body = "\n".join(rows)
    return ("# Concept bindings\n\n"
            "| Concept | Origin | Actions used | Proposal |\n"
            "|---|---|---|---|\n" + body + "\n")


def feature(tmp, rows):
    root = Path(tmp) / "UC-06-x"
    write(root / "stages/01a_responsibility-map/output/responsibility-map.md",
          RESP_MAP)
    write(root / "stages/02_concepts/output/concept-bindings.md", bindings(rows))
    write(root / "stages/02_concepts/output/Profiling.concept.md",
          "concept Profiling [AccountId]\n"
          "purpose\n    to read a profile\n\n"
          "## Actions\n\n```\n"
          "readProfile [ accountId: AccountId ] => [ OK ]\n```\n")
    return str(root)


class ConceptBindingsTests(unittest.TestCase):

    def test_matching_binding_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = feature(tmp, [
                "| `Profiling` | `extends:UC-03-update-profile` | "
                "`readProfile` | `Profiling.concept.md` |"])
            result = run("--feature", f)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS", result.stdout)

    def test_binding_not_in_the_map_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = feature(tmp, [
                "| `GuidelineRules` | `reused:UC-07-maintain-guideline-rules` | "
                "`publishedLineages` | — |"])
            result = run("--feature", f)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not declared in the 01a responsibility map", result.stdout)

    def test_origin_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = feature(tmp, [
                "| `Profiling` | `reused:UC-03-update-profile` | "
                "`readProfile` | — |"])
            result = run("--feature", f)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("but the 01a map says", result.stdout)

    def test_undeclared_action_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = feature(tmp, [
                "| `Profiling` | `extends:UC-03-update-profile` | "
                "`nonexistent` | `Profiling.concept.md` |"])
            result = run("--feature", f)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not declare", result.stdout)


if __name__ == "__main__":
    unittest.main()
