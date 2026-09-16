#!/usr/bin/env python3
"""
verify_shared_action_contracts.py — cross-feature shared-concept drift guard.

Why this exists:
  Concept specs are authored per feature (one `*.concept.md` per UC), but the
  production concept classes are SHARED. Nothing else checks that a concept
  action declared in several features keeps one contract. The conduit rebuild
  experiment hit this (UC-04 `Favoriting.countFor => Counts` vs UC-05
  `=> Counted`), which the per-feature parity/alignment checks cannot see.

What it checks (across every feature's Stage 02 concept specs):
  * For each `Concept.action` declared by >=2 features, the declared OUTCOME
    vocabularies must not be disjoint. Two features giving one action
    completely different outcome tokens is the unambiguous drift (a rename or
    a divergent enum) and FAILS. Subsets (a feature declaring fewer outcomes)
    are fine.
  * Input-parameter NAME sets that are mutually incompatible (neither a subset
    of the other) are reported as WARN — usually an intentional overload, for
    a human to confirm.

Usage:
  python3 verify_shared_action_contracts.py [--features-dir features]
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


def parse_specs(features_dir: str):
    """(concept, action) -> {feature: {'params': set, 'outcomes': set}}."""
    contracts = defaultdict(dict)
    for feature in sorted(os.listdir(features_dir)):
        # UC-00-login is the frozen worked example (pre-v0.6 grammar); it is
        # not part of the live pipeline and is excluded from drift comparison.
        if feature.startswith("UC-00"):
            continue
        spec_dir = os.path.join(features_dir, feature, "stages", "02_concepts", "output")
        if not os.path.isdir(spec_dir):
            continue
        for fname in sorted(os.listdir(spec_dir)):
            m = CONCEPT_FILE.match(fname)
            if not m:
                continue
            concept = m.group(1)
            with open(os.path.join(spec_dir, fname), encoding="utf-8") as fh:
                text = fh.read()
            # An action may declare several signature blocks (modes) — e.g.
            # `Profiling.view` keyed by userId and by username. Union the
            # param sets across every block so an overloaded action's declared
            # surface is the whole set; collapsing to the last block (a dict)
            # reported the earlier modes as drift (the conduit rebuild UC-10 /
            # UC-12 spurious input-shape WARNs).
            signatures = defaultdict(set)
            for action, params in SIGNATURE.findall(text):
                signatures[action] |= _param_names(params)
            effect_tokens = EFFECT_TOKEN.findall(text)
            outcomes = set(OUTCOME.findall(text)) | set(effect_tokens)
            for action, params in signatures.items():
                entry = contracts[(concept, action)].setdefault(
                    feature, {"params": set(), "outcomes": set()})
                entry["params"] |= params
            # distribute the action's outcome tokens to every declared action
            if signatures and outcomes:
                for action in signatures:
                    contracts[(concept, action)][feature]["outcomes"] |= outcomes
    return contracts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Shared-concept action contracts must not drift across features")
    parser.add_argument("--features-dir", default="features")
    args = parser.parse_args()

    contracts = parse_specs(args.features_dir)
    failures, warnings = [], []
    for (concept, action), feats in sorted(contracts.items()):
        if len(feats) < 2:
            continue
        feature_list = sorted(feats)
        # Outcome-vocabulary disjointness -> FAIL.
        for i in range(len(feature_list)):
            for j in range(i + 1, len(feature_list)):
                a, b = feats[feature_list[i]]["outcomes"], feats[feature_list[j]]["outcomes"]
                if a and b and a.isdisjoint(b):
                    failures.append(
                        f"{concept}.{action}: disjoint outcome vocabularies — "
                        f"{feature_list[i]} {sorted(a)} vs {feature_list[j]} {sorted(b)}")
        # Input-name-set incompatibility -> WARN.
        for i in range(len(feature_list)):
            for j in range(i + 1, len(feature_list)):
                a, b = feats[feature_list[i]]["params"], feats[feature_list[j]]["params"]
                if a and b and not (a <= b or b <= a):
                    warnings.append(
                        f"{concept}.{action}: input-shape differs — "
                        f"{feature_list[i]} {sorted(a)} vs {feature_list[j]} {sorted(b)}")

    for w in warnings:
        print(f"WARN  {w}")
    if failures:
        print(f"FAIL  {len(failures)} shared-concept contract drift(s):")
        for f in failures:
            print(f"        {f}")
        print("      Reuse the canonical shared signature/enum, or extend it "
              "additively; do not redeclare an action with a different vocabulary.")
        return 1
    print(f"PASS  shared-concept action contracts consistent "
          f"({sum(1 for k, v in contracts.items() if len(v) > 1)} shared action(s) checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
