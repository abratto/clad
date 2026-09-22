#!/usr/bin/env python3
"""Guard against reintroducing the retired sync-name grammar.

Grammar v3 names a sync action-first and concept-free, with `For<Route>` when the
rule carries a route matcher (`maintenance/sync-name-grammar-v3.md`,
`maintenance/route-scoped-pinned-names.md`). The pre-v3 `For<Scope>` component
(derived from the feature slug) and the condition-first
`When…Then…` header were removed. This test fails if either reappears in a live
authoring surface (`templates/`, `methodology/`).

A line that explicitly narrates the *history* (mentions "removed", "pre-v0.6",
"retired", "historical", "v2", "evolution", "superseded", "frozen") is allowed,
as is a small allow-list of archival documents.
"""

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

# Live authoring surfaces that must not prescribe the retired grammar.
SCAN_DIRS = (REPO_ROOT / "templates", REPO_ROOT / "methodology")

# Archival/evolution documents that legitimately narrate the old grammar.
# (Empty: even the evolution doc now marks its v2 mention as historical, so the
# historical-marker exemption covers it.)
HISTORICAL_FILES = set()

# The retired tokens.
STALE = (
    re.compile(r"For<Scope>"),
    re.compile(r"When<TriggerConcept><TriggerAction><TriggerCompletion>Then<"),
)

# A line that says it is narrating history, not prescribing the grammar.
HISTORICAL_MARKER = re.compile(
    r"removed|pre-v0\.6|retired|historical|v2\b|evolution|superseded|frozen|"
    r"no longer|was removed|survive only",
    re.IGNORECASE,
)


def offending_lines():
    for base in SCAN_DIRS:
        for path in sorted(base.rglob("*.md")):
            if path.name in HISTORICAL_FILES:
                continue
            for number, line in enumerate(
                    path.read_text(encoding="utf-8").splitlines(), start=1):
                if any(pattern.search(line) for pattern in STALE) \
                        and not HISTORICAL_MARKER.search(line):
                    yield f"{path.relative_to(REPO_ROOT)}:{number}: {line.strip()}"


class NoStaleSyncGrammarTests(unittest.TestCase):

    def test_no_for_scope_or_condition_first_grammar_in_live_docs(self):
        offenders = list(offending_lines())
        self.assertEqual(
            offenders, [],
            "retired sync-name grammar (`For<Scope>` / condition-first "
            "`When…Then…`) found in a live authoring surface — use grammar v3 "
            "(`<TargetAction>[For<Route>]When<TriggerAction><TriggerCompletion>`):\n"
            + "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
