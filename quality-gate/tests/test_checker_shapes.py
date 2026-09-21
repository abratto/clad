#!/usr/bin/env python3
"""Locking tests for the shapes the Model B experiment introduced.

Three shapes broke checkers late (maintenance/sync-flow-pinning.md §Review
finding; the Item 3 "checker learns late" pass):

  * the corpus union — a reused concept's spec lives in `features/_system/`,
    not the feature's own output;
  * the flow pin — a non-bootstrap rule's `when` carries an extra last
    `Web/request` conjunct, excluded from the mechanical name;
  * route-scoped names — a bootstrap's name carries `For<Route>`.

These pin the two that had no direct regression test: the pin exclusion in
`verify_implementation_parity.expected_sync_names`, and the corpus union in
`verify_implementation_parity.check_concepts`.
"""

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))

import verify_implementation_parity as parity  # noqa: E402


PINNED_SYNC = """sync CloseWhenVerifyVerified

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `2` | `4` | `MemberEnrolment/verify: [...] => [ Verified ] \u2227 requested: Web/request: [ route: "returns" ] => [ Routed ]` | `Lending/close: [ <args> ]` | `<none>` |

## Rule

```
when {
    MemberEnrolment/verify: [ ... ] => [ Verified ; ... ]
    requested: Web/request: [ route: "returns" ] => [ Routed ; ... ]
}
then {
    Lending/close: [ <args> ]
}
```
"""

BOOTSTRAP_SYNC = """sync VerifyForReturnsWhenRequestRouted

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `1` | `2` | `Web/request: [ route: "returns" ] => [ Routed ]` | `MemberEnrolment/verify: [ <args> ]` | `route = "returns"` |

## Rule

```
when {
    Web/request: [ route: "returns" ] => [ Routed ; ... ]
}
then {
    MemberEnrolment/verify: [ <args> ]
}
```
"""


class MechanicalNameShapeTests(unittest.TestCase):
    """The name a checker derives must know the pin and the route."""

    def _write(self, root, name, text):
        path = root / f"{name}.sync.md"
        path.write_text(text, encoding="utf-8")
        return path

    def test_pin_is_not_a_name_component(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(Path(tmp), "CloseWhenVerifyVerified", PINNED_SYNC)
            names = parity.expected_sync_names(str(path), PINNED_SYNC)
            self.assertIn("CloseWhenVerifyVerified", names)
            self.assertTrue(all("Requested" not in name for name in names), names)
            self.assertTrue(all("ForReturns" not in name for name in names), names)

    def test_route_scoped_bootstrap_name_carries_the_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(Path(tmp), "VerifyForReturnsWhenRequestRouted",
                               BOOTSTRAP_SYNC)
            names = parity.expected_sync_names(str(path), BOOTSTRAP_SYNC)
            self.assertIn("VerifyForReturnsWhenRequestRouted", names)


class ImplementationParityUnionTests(unittest.TestCase):
    """A reused concept has no feature-local spec; the corpus one must count."""

    def _impl(self, root):
        impl = root / "impl"
        impl.mkdir()
        (impl / "WidgetConcept.java").write_text(
            "class WidgetConcept implements Concept {\n}\n", encoding="utf-8")
        return impl

    def test_corpus_spec_satisfies_a_concept_class(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            impl = self._impl(root)
            corpus = root / "features" / "_system" / "concepts"
            corpus.mkdir(parents=True)
            (corpus / "Widget.concept.md").write_text("concept Widget\n",
                                                      encoding="utf-8")
            failures = parity.check_concepts(str(impl), str(root / "features"))
            self.assertEqual(failures, [], failures)

    def test_missing_spec_still_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            impl = self._impl(root)
            (root / "features").mkdir()
            failures = parity.check_concepts(str(impl), str(root / "features"))
            self.assertEqual(len(failures), 1, failures)
            self.assertIn("Widget", failures[0][1])


if __name__ == "__main__":
    unittest.main()
