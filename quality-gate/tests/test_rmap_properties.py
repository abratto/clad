#!/usr/bin/env python3
"""Deterministic property checks for the Python Rmap deriver."""

import random
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))

import rmap  # noqa: E402


def _model(rng, index):
    subject = f"Thing{index}"
    lines = [f"object-type {subject} identified-by {subject}Id"]
    for n in range(rng.randint(1, 6)):
        predicate = f"field{n}"
        value = rng.choice(["String", "Int", "Timestamp"])
        annotation = ["mandatory"] if rng.random() < 0.5 else ["optional"]
        if rng.random() < 0.2:
            annotation.append("unique")
        if value == "Int" and rng.random() < 0.2:
            annotation.append("default 0")
        if rng.random() < 0.15:
            annotation.append("in {a, b, c}")
        lines.append(
            f"fact {predicate} : {subject} -> {value} -- "
            + ", ".join(annotation))
    return f"## Conceptual model\n\n```\n" + "\n".join(lines) + "\n```\n"


class RmapPropertyTests(unittest.TestCase):

    def test_random_simple_models_derive_and_render_deterministically(self):
        rng = random.Random(20261020)
        for index in range(50):
            text = _model(rng, index)
            first = rmap.derive_model(f"Thing{index}", text)
            second = rmap.derive_model(f"Thing{index}", text)
            sql1 = rmap.render_migration("x", [first])
            sql2 = rmap.render_migration("x", [second])
            self.assertEqual(sql1, sql2)
            self.assertIn(f"thing{index}", sql1)
            self.assertTrue(first.tables)
            for column in first.tables[0].columns:
                self.assertTrue(column.column)

    def test_mandatory_toggle_changes_sql(self):
        base = """## Conceptual model

```
object-type E identified-by EId
fact value : E -> String -- optional
```
"""
        changed = base.replace("-- optional", "-- mandatory")
        a = rmap.render_migration("x", [rmap.derive_model("E", base)])
        b = rmap.render_migration("x", [rmap.derive_model("E", changed)])
        self.assertNotEqual(a, b)
        self.assertIn("NOT NULL", b)

    def test_compound_and_multi_shapes_are_stable(self):
        text = """## Conceptual model

```
object-type A identified-by AId
object-type B identified-by BId
fact pair : ( A, B ) -> Int -- mandatory
fact tags : A -> { Tag } -- zero or more
```
"""
        one = rmap.render_migration("x", [rmap.derive_model("Shape", text)])
        two = rmap.render_migration("x", [rmap.derive_model("Shape", text)])
        self.assertEqual(one, two)
        self.assertIn("PRIMARY KEY", one)


if __name__ == "__main__":
    unittest.main()
