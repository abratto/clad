#!/usr/bin/env python3
"""A lightweight mutation check: known Rmap defects must change output.

This is not a full mutation-score tool; it proves the golden/property suite's
critical rules are not vacuous by loading a few mutated copies of rmap.py and
asserting the rendered schema differs from the baseline.
"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
RMAP = QUALITY_GATE / "rmap.py"
sys.path.insert(0, str(QUALITY_GATE))

import rmap  # noqa: E402

MODEL = """## Conceptual model

```
object-type E identified-by EId
object-type F identified-by FId
fact count : E -> Int -- mandatory, default 0
fact state : E -> State -- mandatory, in {open, closed}
fact pair : ( E, F ) -> Int -- optional
fact copy : E -> Copy -- mandatory, unique while returnedAt absent
fact returnedAt : E -> Timestamp -- optional
fact tags : E -> { Tag } -- zero or more
```
"""


def _load_mutated(source):
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".py", delete=False, encoding="utf-8")
    try:
        handle.write(source)
        handle.close()
        spec = importlib.util.spec_from_file_location(
            "rmap_mutation", handle.name)
        module = importlib.util.module_from_spec(spec)
        sys.modules["rmap_mutation"] = module
        spec.loader.exec_module(module)
        return module
    finally:
        try:
            __import__("os").unlink(handle.name)
        except OSError:
            pass


class RmapMutationSensitivityTests(unittest.TestCase):

    def setUp(self):
        self.baseline = rmap.render_migration(
            "x", [rmap.derive_model("Shape", MODEL)])

    def _assert_mutant_changes_output(self, old, new):
        source = RMAP.read_text()
        self.assertIn(old, source)
        mutated = _load_mutated(source.replace(old, new, 1))
        output = mutated.render_migration(
            "x", [mutated.derive_model("Shape", MODEL)])
        self.assertNotEqual(output, self.baseline,
                            f"mutation was not detected: {old} -> {new}")

    def test_int_type_mutation(self):
        self._assert_mutant_changes_output('return "INTEGER"', 'return "TEXT"')

    def test_enum_mutation(self):
        self._assert_mutant_changes_output(
            'return f"{column} IN (', 'return f"{column} NOT IN (')

    def test_filtered_unique_mutation(self):
        self._assert_mutant_changes_output(
            '" IS NULL"', '" IS NOT NULL"')

    def test_compound_subject_mutation(self):
        self._assert_mutant_changes_output(
            "        if fact.compound:\n",
            "        if False and fact.compound:\n")


if __name__ == "__main__":
    unittest.main()
