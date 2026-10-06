#!/usr/bin/env python3
"""
concept_remodel.py — shared mechanics for the `remodel` proposal class
(maintenance change `concept-remodel-class`, R22 amendment).

A `remodel:UC-XX` origin is the deliberate, reviewable path for a
NON-additive change to a canonical concept — the middle ground between an
additive `extends` and the heavyweight R20 maintenance route. Two
obligations make it deliberate:

  1. **Migration notes.** The proposal spec carries a `## Migration notes`
     section listing, per dropped or restated canonical line (state lines
     and contract actions/outcomes), the exact line in backticks with a
     reason. The additivity gate subtracts exactly the noted lines and
     still fails on anything unnoted — the same "visible and bounded"
     contract `_config/additivity-exceptions.md` gives an extend, but
     carried on the proposal itself.
  2. **Consent.** Promotion requires a consent receipt from every feature
     on the concept's canonical history (`introduced-by` /
     `extended-by`, minus the proposer), recorded at
     `features/_system/concepts/_remodel-consent/<Concept>-<feature>.md`.
     A remodel rewrites what earlier features built on; their sign-off is
     the review.

An `extends` is NEVER rescued by remodel mechanics: consent receipts and
migration notes apply to `remodel` rows only.

Imported by verify_concept_additivity.py (Gate-2/3 check) and
promote_concepts.py (promotion refusal).
"""

from __future__ import annotations

import os
import re
from typing import List, Set, Tuple

import artifact_parsers as ap
import verify_concept_additivity as vca

MIGRATION_SECTION = re.compile(r"^##\s+Migration notes\s*$(.*?)(?=^##\s|\Z)",
                               re.MULTILINE | re.DOTALL)

CONSENT_DIRNAME = "_remodel-consent"


def is_remodel(origin: str) -> bool:
    return (origin or "").strip().lower().startswith("remodel")


def migration_notes(spec_text: str) -> Set[str]:
    """The normalised backticked lines the proposal's `## Migration notes`
    authorises dropping/restating. Empty when the section is absent."""
    section = MIGRATION_SECTION.search(spec_text)
    if not section:
        return set()
    noted: Set[str] = set()
    for line in section.group(1).splitlines():
        stripped = line.strip()
        if not stripped.startswith(("-", "*")):
            continue
        noted.update(vca._normalised(m)
                     for m in re.findall(r"`([^`]+)`", stripped))
    return noted


def consent_dir(corpus: str) -> str:
    return os.path.join(corpus, CONSENT_DIRNAME)


def history_features(corpus: str, concept: str) -> List[str]:
    """The concept's canonical history: introducer first, then extenders in
    promotion order, deduplicated. Empty when no canonical spec exists."""
    canonical = os.path.join(corpus, concept + ".concept.md")
    if not os.path.isfile(canonical):
        return []
    import promote_concepts as pc
    with open(canonical, encoding="utf-8") as handle:
        text = handle.read()
    features: List[str] = []
    intro = pc.INTRODUCED_RE.search(text)
    if intro:
        features.append(intro.group(1).strip())
    ext = pc.EXTENDED_RE.search(text)
    if ext:
        features.extend(s.strip() for s in ext.group(1).split(","))
    # Deduplicate, preserving order (a feature may appear twice in history).
    seen, ordered = set(), []
    for feature in features:
        if feature and feature not in seen:
            seen.add(feature)
            ordered.append(feature)
    return ordered


def missing_consent(corpus: str, concept: str, proposer: str) -> List[str]:
    """Historical features (other than the proposer) whose consent receipt
    for this remodel is absent."""
    directory = consent_dir(corpus)
    missing = []
    for feature in history_features(corpus, concept):
        if feature == proposer:
            continue
        receipt = os.path.join(directory, f"{concept}-{feature}.md")
        if not os.path.isfile(receipt):
            missing.append(feature)
    return missing


def _term_covered(term: str, noted: Set[str]) -> bool:
    """A dropped contract term is covered when every backticked span it
    names (`verify` in `action \`verify\``; `REFUSED` and `check` in
    `outcome \`REFUSED\` of \`check\``) appears among the noted spans."""
    spans = re.findall(r"`([^`]+)`", term)
    return bool(spans) and all(span in noted for span in spans)


def unauthorised_drops(feature_root: str, corpus: str,
                       concept: str) -> Tuple[List[str], List[str]]:
    """(state drops, contract-term drops) NOT covered by the proposal's
    migration notes."""
    proposal = os.path.join(feature_root, "stages", "02_concepts", "output",
                            concept + ".concept.md")
    noted: Set[str] = set()
    if os.path.isfile(proposal):
        with open(proposal, encoding="utf-8") as handle:
            noted = migration_notes(handle.read())
    state = [line for line in
             vca.dropped_state_lines(feature_root, corpus, concept)
             if line not in noted]
    terms = [term for term in
             vca.dropped_contract_terms(feature_root, corpus, concept)
             if term != "<entire contract missing>"
             and not _term_covered(term, noted)]
    if "<entire contract missing>" in vca.dropped_contract_terms(
            feature_root, corpus, concept):
        terms.append("<entire contract missing>")
    return state, terms
