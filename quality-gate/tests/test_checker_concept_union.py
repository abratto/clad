#!/usr/bin/env python3
"""Enforce checker shape-awareness as a durable invariant.

The Model B / grammar work introduced three shapes that checkers have to know
(methodology/implementation/QUALITY_GATE.md §"Checker shape-awareness"):

  * the corpus union — a concept's spec/contract is in the feature's
    `02_concepts/output/` or the canonical `features/_system/concepts/`;
  * the flow pin — a non-bootstrap `when` carries a `requested: Web/request: …`
    conjunct (last), excluded from the name;
  * route-scoped names — `For<Route>` on bootstraps and pinned rules.

A checker that reads a concept/contract spec but resolves only one directory is
the recurring defect this guards. This test is a registry: every concept/contract
reader must either use the union resolver or be listed with a reason. It fails
when a *new* checker is added without considering the shapes.
"""

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"

# A source that reads a concept or contract artefact.
CONCEPT_READER = re.compile(
    r"parse_concept|parse_spec|concept_spec_paths|concept_source_dirs|"
    r"\.concept\.md|\.contract\.md")

# Tokens that mean "this checker resolves the corpus union".
UNION_TOKENS = (
    "concept_source_dirs", "merge_by_concept", "contract_actions",
    "parse_spec_outcomes_multi", "--concept-dir", "--contract-dir", "_system",
)

# Checkers that read a concept/contract artefact but do not need the union.
UNION_EXEMPT = {
    "verify_concept_additivity.py":
        "compares the feature proposal against the canonical corpus by design",
    "verify_concept_registry.py":
        "reads the corpus and each feature's proposals by design",
    "verify_concept_corpus_current.py":
        "the corpus-currency check; reads the corpus and each feature's proposals by design",
    "verify_concept_proposals.py":
        "reads only the feature's own proposals and the responsibility map",
    "verify_iterative_change_coupling.py":
        "matches both the feature spec and the corpus spec by path",
    "verify_file_manifest.py":
        "generic file-presence check; does not resolve concepts",
    "verify_links.py":
        "documentation link check; does not resolve concepts",
}

# Checkers that derive a sync name and must use the shared stem (which knows
# the pin and the route).
NAME_DERIVERS = ("verify_implementation_parity.py",)


def concept_readers():
    for path in sorted(QG.glob("verify_*.py")):
        if CONCEPT_READER.search(path.read_text(encoding="utf-8")):
            yield path


class CheckerShapeAwarenessTests(unittest.TestCase):

    def test_every_concept_reader_is_union_aware_or_exempt(self):
        failures = []
        for path in concept_readers():
            text = path.read_text(encoding="utf-8")
            if path.name in UNION_EXEMPT:
                continue
            if not any(token in text for token in UNION_TOKENS):
                failures.append(
                    f"{path.name}: reads a concept/contract artefact but does not "
                    f"resolve the corpus union (add a --concept-dir/--contract-dir "
                    f"resolver, or list it in UNION_EXEMPT with a reason)")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_exemptions_are_live_and_justified(self):
        # No stale exemptions: every exempt name must be a real concept reader.
        readers = {p.name for p in concept_readers()}
        for name, reason in UNION_EXEMPT.items():
            self.assertIn(name, readers,
                          f"stale exemption: {name} no longer reads concept specs")
            self.assertTrue(reason.strip(), f"{name} exemption has no reason")

    def test_name_derivers_use_the_shared_stem(self):
        for name in NAME_DERIVERS:
            text = (QG / name).read_text(encoding="utf-8")
            self.assertIn("sync_stem", text,
                          f"{name} derives a sync name without the shared "
                          f"sync_stem (which knows the pin and the route)")


if __name__ == "__main__":
    unittest.main()
