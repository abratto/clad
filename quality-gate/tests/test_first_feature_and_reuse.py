#!/usr/bin/env python3
"""Regression coverage for D8 (first-feature checks) and D43 (reused contract)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QG))

import clad_stages as cs  # noqa: E402
REUSED = QG / "verify_reused_concept_contracts.py"


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *map(str, args)],
                          cwd=REPO_ROOT, capture_output=True, text=True)


class FirstFeatureRequiresTests(unittest.TestCase):

    def test_concept_requires_excludes_empty_corpus(self):
        """D8: the feature's own Stage-02 output is required even when the
        canonical corpus is empty, so first-feature checks run instead of
        silently skipping."""
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "features/UC-01-first"
            output = feature / "stages/02_concepts/output"
            output.mkdir(parents=True)
            (output / "Foo.concept.md").write_text("concept Foo\n", encoding="utf-8")
            # corpus absent
            reqs = cs._concept_source_requires(str(feature))
            self.assertIn(str(output), reqs)
            self.assertEqual(len(reqs), 1, reqs)


class ReusedConceptContractTests(unittest.TestCase):

    def _feature(self, tmp, origin):
        feature = Path(tmp) / "features/UC-04-reuse"
        (feature / "stages/01a_responsibility-map/output").mkdir(parents=True)
        (feature / "stages/01a_responsibility-map/output/responsibility-map.md").write_text(
            "# Responsibility map\n\n"
            "| Concept | Origin | Owned state (one line) | Owned actions | Notes |\n"
            "|---|---|---|---|---|\n"
            f"| `Multi` | `{origin}` | x | `run` | n |\n",
            encoding="utf-8")
        (Path(tmp) / "features/_system/concepts").mkdir(parents=True)
        return feature, Path(tmp) / "features/_system/concepts"

    def test_reused_without_canonical_contract_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature, _corpus = self._feature(tmp, "reused:UC-01")
            r = run(REUSED, "--feature", feature)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_reused_with_canonical_contract_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature, corpus = self._feature(tmp, "reused:UC-01")
            (corpus / "Multi.contract.md").write_text("contract\n", encoding="utf-8")
            r = run(REUSED, "--feature", feature)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_new_concept_needs_no_canonical_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature, _corpus = self._feature(tmp, "new")
            r = run(REUSED, "--feature", feature)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
