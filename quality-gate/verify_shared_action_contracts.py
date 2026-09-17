#!/usr/bin/env python3
"""
verify_shared_action_contracts.py — canonical-corpus / proposal drift guard.

Why this exists:
  Concept classes are SHARED across features. The conduit rebuild experiment hit
  two features giving one concept action different outcome vocabularies
  (UC-04 `Favoriting.countFor => Counts` vs UC-05 `=> Counted`), invisible to the
  per-feature parity/alignment checks.

  Under the system-scope concept model (maintenance change
  `system-scope-concept-vocabulary`) the canonical spec lives once in
  `features/_system/concepts/`, and a feature that needs a new action/outcome
  emits a PROPOSAL in its own `02_concepts/output/`. Drift is therefore no
  longer "two features disagree" but "a proposal diverges from the corpus" —
  this guard compares both:

    * the canonical corpus (labelled `corpus`), and
    * every feature's own Stage-02 concept specs (its proposals, or — for a
      pre-Model-B feature — its full per-feature specs).

What it checks (per `Concept.action` declared by >=2 sources):
  * OUTCOME vocabularies must not be DISJOINT. A proposal (or a legacy feature)
    giving an action completely different outcome tokens from the corpus is the
    unambiguous drift (a rename or a divergent enum) and FAILS. Subsets are fine
    (a feature declaring fewer outcomes, or a proposal adding tokens).
  * Input-parameter NAME sets that are mutually incompatible (neither a subset
    of the other) are reported as WARN — usually an intentional overload.

Usage:
  python3 verify_shared_action_contracts.py [--features-dir features]
                                            [--concepts-dir features/_system/concepts]
"""

import argparse
import os
import re
import sys
from collections import defaultdict

CONCEPT_FILE = re.compile(r"(.+)\.concept\.md$")
# `action [ <params> ]` — the input side of an action signature line.
SIGNATURE = re.compile(r"^(\w+)\s*\[([^\]]*)\]", re.MULTILINE)
# `outcome: "Token(...)"` / `outcome: "Token"` in a flow-token line.
OUTCOME = re.compile(r'outcome:\s*"([A-Za-z][A-Za-z0-9_]*)')
# `action [ ... ] => [ Token(...) ]` — the effect-first token, where present.
EFFECT_TOKEN = re.compile(r"\]\s*=>\s*\[\s*([A-Z][A-Za-z0-9_]*)")

CORPUS_LABEL = "corpus"


def _param_names(params: str):
    names = set()
    for part in params.split(";"):
        part = part.strip()
        if not part:
            continue
        name = re.split(r"[:=]", part, 1)[0].strip().strip("?")
        if re.fullmatch(r"[A-Za-z_]\w*", name):
            names.add(name)
    return names


def parse_dir(concept_dir: str, label: str, contracts):
    """Fold every `*.concept.md` in one directory into `contracts` under
    `label`: (concept, action) -> {label: {'params': set, 'outcomes': set}}."""
    if not os.path.isdir(concept_dir):
        return
    for fname in sorted(os.listdir(concept_dir)):
        if not CONCEPT_FILE.match(fname):
            continue
        concept = CONCEPT_FILE.match(fname).group(1)
        with open(os.path.join(concept_dir, fname), encoding="utf-8") as fh:
            text = fh.read()
        # An action may declare several signature blocks (modes) — e.g.
        # `Profiling.view` keyed by userId and by username. Union the param sets
        # across every block so an overloaded action's declared surface is the
        # whole set; collapsing to the last block (a dict) reported the earlier
        # modes as drift (the conduit rebuild UC-10 / UC-12 spurious WARNs).
        signatures = defaultdict(set)
        for action, params in SIGNATURE.findall(text):
            signatures[action] |= _param_names(params)
        effect_tokens = EFFECT_TOKEN.findall(text)
        outcomes = set(OUTCOME.findall(text)) | set(effect_tokens)
        for action, params in signatures.items():
            entry = contracts[(concept, action)].setdefault(
                label, {"params": set(), "outcomes": set()})
            entry["params"] |= params
        # distribute the action's outcome tokens to every declared action
        if signatures and outcomes:
            for action in signatures:
                contracts[(concept, action)][label]["outcomes"] |= outcomes


def parse_specs(features_dir: str, concepts_dir: str):
    """(concept, action) -> {source_label: {'params': set, 'outcomes': set}}.

    Sources are the canonical corpus plus every feature's Stage-02 specs.
    UC-00-login is the frozen worked example (pre-v0.6 grammar); it is excluded
    from drift comparison."""
    contracts = defaultdict(dict)
    parse_dir(concepts_dir, CORPUS_LABEL, contracts)
    if not os.path.isdir(features_dir):
        return contracts
    for feature in sorted(os.listdir(features_dir)):
        if feature.startswith("UC-00"):
            continue
        concept_dir = os.path.join(features_dir, feature, "stages", "02_concepts",
                                "output")
        parse_dir(concept_dir, feature, contracts)
    return contracts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Canonical concept/proposal action contracts must not drift")
    parser.add_argument("--features-dir", default="features")
    parser.add_argument("--concepts-dir", default=None,
                        help="Canonical corpus (default <features-dir>/_system/concepts)")
    args = parser.parse_args()

    concepts_dir = args.concepts_dir or os.path.join(args.features_dir,
                                                     "_system", "concepts")
    contracts = parse_specs(args.features_dir, concepts_dir)
    failures, warnings = [], []
    for (concept, action), sources in sorted(contracts.items()):
        if len(sources) < 2:
            continue
        labels = sorted(sources)
        # Outcome-vocabulary disjointness -> FAIL.
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                a = sources[labels[i]]["outcomes"]
                b = sources[labels[j]]["outcomes"]
                if a and b and a.isdisjoint(b):
                    failures.append(
                        f"{concept}.{action}: disjoint outcome vocabularies — "
                        f"{labels[i]} {sorted(a)} vs {labels[j]} {sorted(b)}")
        # Input-name-set incompatibility -> WARN.
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                a = sources[labels[i]]["params"]
                b = sources[labels[j]]["params"]
                if a and b and not (a <= b or b <= a):
                    warnings.append(
                        f"{concept}.{action}: input-shape differs — "
                        f"{labels[i]} {sorted(a)} vs {labels[j]} {sorted(b)}")

    for w in warnings:
        print(f"WARN  {w}")
    if failures:
        print(f"FAIL  {len(failures)} shared-concept contract drift(s):")
        for f in failures:
            print(f"        {f}")
        print("      Reuse the canonical signature/enum, or extend it "
              "additively; do not redeclare an action with a different vocabulary.")
        return 1
    print(f"PASS  concept action contracts consistent "
          f"({sum(1 for v in contracts.values() if len(v) > 1)} shared action(s) checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
