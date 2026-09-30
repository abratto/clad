#!/usr/bin/env python3
"""Regression: a stage with no expected outputs is skipped, not failed.

An unchanged-state extend produces no Stage 03b data model. The `_DATA_MODEL`
check must skip (sentinel requires) rather than run on an empty output dir and
fail — the same pattern `_manifest_check` already uses.
"""

import sys
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"


class NoExpectedOutputCheckTests(unittest.TestCase):

    def setUp(self):
        sys.path.insert(0, str(QG))
        import clad_stages as cs
        self.cs = cs

    def test_data_model_check_skips_when_no_state_owning_concept(self):
        with mock.patch.object(self.cs, "feature_model_concepts", return_value=[]):
            requires = self.cs._DATA_MODEL.requires("/tmp/feature")
        self.assertTrue(
            any("__no_expected_outputs__" in p for p in requires),
            requires)

    def test_data_model_check_runs_when_a_concept_owns_state(self):
        with mock.patch.object(self.cs, "feature_model_concepts",
                               return_value=["Widget"]):
            requires = self.cs._DATA_MODEL.requires("/tmp/feature")
        self.assertFalse(
            any("__no_expected_outputs__" in p for p in requires),
            requires)


if __name__ == "__main__":
    unittest.main()
