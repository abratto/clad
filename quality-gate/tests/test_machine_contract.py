#!/usr/bin/env python3
"""Compatibility checks for CLAD's machine-facing feature descriptor."""

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DESCRIBE = REPO_ROOT / "quality-gate" / "describe_feature.py"
VERIFY_CHAIN = REPO_ROOT / "quality-gate" / "verify_chain_grammar.py"
FEATURE = REPO_ROOT / "examples" / "UC-00-login"


class MachineContractTests(unittest.TestCase):

    def test_feature_descriptor_has_versioned_envelope(self):
        result = subprocess.run(
            [sys.executable, str(DESCRIBE), "--feature", str(FEATURE)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        descriptor = json.loads(result.stdout)
        contract = descriptor["contract"]
        self.assertEqual(contract["name"], "clad.feature-descriptor")
        self.assertEqual(contract["version"], 1)
        self.assertIn("action-outcomes.v1", contract["capabilities"])

        expected = descriptor["expectedOutputs"]
        # Keyed by canonical stage id, not a directory name.
        self.assertIn("03a", expected)
        self.assertNotIn("03a_dependency-review", expected)
        self.assertIn("Web-card.md", expected["03a"])
        self.assertIn("concept-matrix.md", expected["03a"])

    def test_chain_grammar_accepts_canonical_feature(self):
        result = subprocess.run(
            [sys.executable, str(VERIFY_CHAIN),
             "--chain-dir", str(FEATURE / "stages/01b_chain-table/output")],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()