#!/usr/bin/env python3
"""Regression coverage for verify_concept_criteria.py's external-type check.

The check flags a state/action TYPE named after another concept (R1). It must
read type POSITIONS, not every capitalised word — a concept name mentioned in a
section's prose is not a type reference.
"""

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QG))

import verify_concept_criteria as criteria  # noqa: E402


def spec(name, state_body):
    return (
        f"concept {name} [UserId]\n"
        "purpose\n    to guard a thing well and clearly\n\n"
        "## State\n\n```\n" + state_body + "\n```\n\n"
        "## Actions\n\n```\n"
        f"{name.lower()} [ userId: UserId ] => [ ok ]\n"
        f'    flow token: {{ action: "{name}.{name.lower()}", userId, outcome: "OK" }}\n'
        "```\n\n"
        "## Operational principle\n\n```\n"
        f"after  {name}/{name.lower()}: [ userId: u ] => [ ok ]\n"
        "```\n")


class ConceptCriteriaExternalTypeTests(unittest.TestCase):

    def _failures(self, tmp, name, state_body, others):
        path = Path(tmp) / f"{name}.concept.md"
        path.write_text(spec(name, state_body), encoding="utf-8")
        failures, _warnings = criteria.check_one(str(path), set(others))
        return failures

    def test_a_concept_name_in_prose_is_not_an_external_type(self):
        # `GuidelineRules` is mentioned in a note, not used as a type.
        state = ("sex: UserId -> SexValue   -- mandatory\n"
                 "-- lineages are resolved from GuidelineRules by the sync")
        failures = self._failures(
            tempfile.mkdtemp(), "Profiling", state, {"Profiling", "GuidelineRules"})
        self.assertEqual(failures, [])

    def test_an_external_type_in_a_state_relation_is_flagged(self):
        state = "sex: UserId -> GuidelineRules   -- mandatory"
        failures = self._failures(
            tempfile.mkdtemp(), "Profiling", state, {"Profiling", "GuidelineRules"})
        self.assertTrue(any("external type" in f for f in failures), failures)


if __name__ == "__main__":
    unittest.main()
