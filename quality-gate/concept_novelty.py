#!/usr/bin/env python3
"""
concept_novelty.py — shared overlap logic for the concept-novelty gate and
the concept-overlap linter (maintenance change `concept-novelty-gate`).

A NEW concept proposal must justify why nothing in the canonical corpus
already fits. "Already fits" is approximated by token overlap between the
proposal (name + declared action names) and each catalog row (concept name +
its action names), scored with the Jaccard index. The threshold comes from
`clad.properties` (`concept.novelty.threshold`, default 0.5).

This module is imported by:
  * verify_concept_novelty.py  — blocking Gate-1 check
  * lint_concept_overlap.py    — advisory linter (exit 0 always)

Not wired to the generator: the catalog is derived
(`generate_concepts_catalog.py`), so the token sets are always computed from
the catalog file on disk; staleness is the registry check's concern
(`verify_concept_registry.py` catalog completeness), not duplicated here.
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Set, Tuple

_WORD = re.compile(r"[A-Za-z][a-z0-9]*")

DEFAULT_THRESHOLD = 0.5


def word_tokens(text: str) -> Set[str]:
    """Lowercase word tokens: PascalCase/camelCase are split at capitals, so
    `lookupByUsername` yields {lookup, by, username}."""
    return {tok.lower() for tok in _WORD.findall(text or "")}


def proposal_tokens(name: str, actions: List[str]) -> Set[str]:
    """Token set for a proposal: its name plus its declared action names."""
    tokens = word_tokens(name)
    for action in actions:
        tokens |= word_tokens(action)
    return tokens


def load_catalog_tokens(catalog_path: str) -> Dict[str, Set[str]]:
    """Concept -> token set, parsed from the generated concepts-catalog.md.

    Columns: Concept | Purpose | Type params | Actions | Introduced by |
    Used by | Notes. Only the Concept and Actions columns contribute tokens.
    Empty dict when the catalog is absent (a project's first feature).
    """
    entries: Dict[str, Set[str]] = {}
    if not os.path.isfile(catalog_path):
        return entries
    with open(catalog_path, encoding="utf-8") as fh:
        in_table = False
        for line in fh:
            if line.lstrip().startswith("| Concept |"):
                in_table = True
                continue
            if in_table:
                if re.match(r"^\|[\s\-:]+\|", line):
                    continue
                if not line.startswith("|"):
                    in_table = False
                    continue
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) < 4:
                    continue
                concept = cells[0].strip("`").strip()
                if not concept:
                    continue
                actions = re.findall(r"`([^`]+)`", cells[3])
                entries[concept] = proposal_tokens(concept, actions)
    return entries


def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def near_matches(tokens: Set[str], catalog: Dict[str, Set[str]],
                 threshold: float) -> List[Tuple[str, float]]:
    """Catalog concepts whose token overlap with `tokens` meets the
    threshold, sorted by descending score then name (deterministic)."""
    matches = [(concept, jaccard(tokens, entry))
               for concept, entry in catalog.items()]
    matches = [(c, s) for c, s in matches if s >= threshold]
    return sorted(matches, key=lambda pair: (-pair[1], pair[0]))


def parse_threshold(raw: str) -> float:
    """Parse the configured threshold; fall back to the default on junk."""
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return DEFAULT_THRESHOLD
    return value if 0.0 < value <= 1.0 else DEFAULT_THRESHOLD
