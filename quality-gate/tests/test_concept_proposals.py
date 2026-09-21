#!/usr/bin/env python3
"""Regression coverage for verify_concept_proposals.py.

A feature's `<Name>.concept.md` is a *proposal snapshot*; the corpus copy is
canonical (maintenance/concept-provenance-and-additivity.md). While Gate 2 is
open the proposal must carry the `proposal snapshot` header the Stage-02
template stamps, so a reader can tell the two copies apart; a feature whose
Gate 2 is already approved is grandfathered.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
TEMPLATE = REPO_ROOT / "templates" / "concept.md"

RESP_MAP = """# Responsibility map — UC-01-a

## Concepts

| Concept | Origin | Owned state (one line) | Owned actions | Notes |
|---|---|---|---|---|
| `Widget` | `new` | `widgets: Map<WidgetId, Widget>` | `check` | x |
"""

STAMPED = ("<!-- proposal snapshot — derived from templates/concept.md; "
           "canonical spec: features/_system/concepts/Widget.concept.md -->\n\n"
           "concept Widget [WidgetId]\nintroduced-by UC-01-a\n")
UNSTAMPED = "concept Widget [WidgetId]\nintroduced-by UC-01-a\n"


def run(*args):
    return subprocess.run(
        [sys.executable, str(QG / "verify_concept_proposals.py"), *args],
        cwd=REPO_ROOT, capture_output=True, text=True)


class ConceptProposalStampTests(unittest.TestCase):

    def _feature(self, root, proposal, resume):
        feature = root / "UC-01-a"
        (feature / "stages/01a_responsibility-map/output").mkdir(parents=True)
        (feature / "stages/02_concepts/output").mkdir(parents=True)
        (feature / "stages/01a_responsibility-map/output/responsibility-map.md"
         ).write_text(RESP_MAP, encoding="utf-8")
        (feature / "stages/02_concepts/output/Widget.concept.md"
         ).write_text(proposal, encoding="utf-8")
        (feature / "RESUME.md").write_text(resume, encoding="utf-8")
        return feature

    def test_template_carries_the_proposal_stamp(self):
        self.assertIn("proposal snapshot", TEMPLATE.read_text(encoding="utf-8"))

    def test_open_gate_requires_the_stamp(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(
                Path(temporary), UNSTAMPED,
                "# RESUME\n\n- **Gate 1 (Requirements):** `approved`\n")
            result = run("--feature", str(feature))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("proposal snapshot", result.stdout)

    def test_open_gate_stamped_proposal_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(
                Path(temporary), STAMPED,
                "# RESUME\n\n- **Gate 1 (Requirements):** `approved`\n")
            result = run("--feature", str(feature))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_approved_gate_grandfathers_an_unstamped_proposal(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(
                Path(temporary), UNSTAMPED,
                "# RESUME\n\n- **Gate 2 (Architecture):** `approved`\n")
            result = run("--feature", str(feature))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
