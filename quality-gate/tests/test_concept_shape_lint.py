#!/usr/bin/env python3
"""Regression coverage for the shape lints added to
verify_concept_criteria.py (maintenance change `concept-shape-lint`).

All shape lints are advisory WARNings — granularity is human judgment; the
lint surfaces smells (machinery suffixes, over-long purposes, degenerate
operational principles, over-wide state/action surfaces) without blocking.
The UC-00-login canonical specs must produce zero warnings.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
EXAMPLE_CONCEPTS = (REPO_ROOT / "examples" / "UC-00-login" / "stages"
                    / "02_concepts" / "output")

CLEAN = """concept WidgetNaming [WidgetId]
purpose
    to associate widget names with opaque identifiers

## State

```
name: WidgetId -> String   -- mandatory
```

## Actions

```
register [ name: String ] => [ widgetId: WidgetId ]
    precondition {
        name not in Cod(State.name)
    }
    postcondition {
        State.name'[widgetId] = name
    }

lookupByName [ name: String ] => [ widgetId: WidgetId ]
    precondition {
        name in Dom(State.name)
    }
    no state change
```

## Operational principle

```
after  WidgetNaming/register:      [ name: "w" ] => [ widgetId: w ]
then  WidgetNaming/lookupByName:   [ name: "w" ] => [ widgetId: w ]
```
"""

MACHINERY = CLEAN.replace("concept WidgetNaming [WidgetId]",
                          "concept WidgetService [WidgetId]")

LONG_PURPOSE = CLEAN.replace(
    "to associate widget names with opaque identifiers",
    "to associate widget names with opaque identifiers and also to "
    "validate those names against policy and to audit every lookup that "
    "any caller performs")

DEGENERATE_PRINCIPLE = CLEAN.replace(
    """after  WidgetNaming/register:      [ name: "w" ] => [ widgetId: w ]
then  WidgetNaming/lookupByName:   [ name: "w" ] => [ widgetId: w ]""",
    """after  WidgetNaming/register:      [ name: "w" ] => [ widgetId: w ]""")

WIDE_STATE = CLEAN.replace(
    "name: WidgetId -> String   -- mandatory",
    "\n".join(f"field{i}: WidgetId -> String   -- mandatory"
              for i in range(9)))

BROAD_ACTIONS = CLEAN.replace(
    "lookupByName [ name: String ] => [ widgetId: WidgetId ]",
    "\n\n".join(f"action{i} [ name: String ] => [ widgetId: WidgetId ]"
                for i in range(11))).replace(
    # keep the principle citing two declared actions so only the count warns
    "then  WidgetNaming/lookupByName:   [ name: \"w\" ] => [ widgetId: w ]",
    "then  WidgetNaming/action0:        [ name: \"w\" ] => [ widgetId: w ]")


def run(*args):
    return subprocess.run(
        [sys.executable, str(QG / "verify_concept_criteria.py"), *args],
        cwd=REPO_ROOT, capture_output=True, text=True)


class ConceptShapeLintTests(unittest.TestCase):

    def _concept_dir(self, root, text):
        directory = Path(root) / "concepts"
        directory.mkdir()
        (directory / "WidgetNaming.concept.md").write_text(
            text, encoding="utf-8")
        return str(directory)

    def _warnings(self, root, text):
        result = run("--concept-dir", self._concept_dir(root, text))
        self.assertEqual(result.returncode, 0,
                         result.stdout + result.stderr)
        return result.stdout

    def test_clean_spec_produces_no_warnings(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = self._warnings(temporary, CLEAN)
            self.assertIn("PASS", output)
            self.assertIn("0 warning(s)", output)

    def test_machinery_suffix_warns(self):
        with tempfile.TemporaryDirectory() as temporary:
            text = MACHINERY.replace("WidgetNaming.concept", "WidgetService.concept")
            directory = Path(temporary) / "concepts"
            directory.mkdir()
            (directory / "WidgetService.concept.md").write_text(
                text, encoding="utf-8")
            result = run("--concept-dir", str(directory))
            self.assertEqual(result.returncode, 0)
            self.assertIn("machinery suffix", result.stdout)

    def test_long_purpose_warns(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = self._warnings(temporary, LONG_PURPOSE)
            self.assertIn("purpose is", output)

    def test_degenerate_principle_warns(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = self._warnings(temporary, DEGENERATE_PRINCIPLE)
            self.assertIn("degenerates", output)

    def test_wide_state_warns(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = self._warnings(temporary, WIDE_STATE)
            self.assertIn("state fields", output)

    def test_broad_action_surface_warns(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = self._warnings(temporary, BROAD_ACTIONS)
            self.assertIn("actions (limit", output)

    def test_canonical_example_specs_produce_no_warnings(self):
        result = run("--concept-dir", str(EXAMPLE_CONCEPTS))
        self.assertEqual(result.returncode, 0,
                         result.stdout + result.stderr)
        self.assertIn("0 warning(s)", result.stdout)


if __name__ == "__main__":
    unittest.main()
