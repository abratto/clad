#!/usr/bin/env python3
"""
describe_feature.py — emit a single JSON descriptor of a CLAD feature.

This is the machine-facing summary that a CLAD-consuming runtime (e.g. the
clad-agent) uses instead of re-implementing the markdown grammar in its own
language. It delegates to artifact_parsers.py, so the parsing grammar lives in
exactly one place (CLAD Python).

The descriptor contains everything a downstream agent needs to know which
artefacts a feature already has and which it is expected to produce:

  concepts  : [ { name, actions: [...] } ]   (business concepts, Web excluded)
  scenarios : [ <name> ]                     (from usecase.md)
  syncs     : [ { name, trigger, then } ]    (from 03_syncs/output)
  expected_outputs : { <stage-id>: [ filenames ] }   (what each stage produces)

Usage:
  python3 quality-gate/describe_feature.py --feature <features/UC-XX-slug>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List

import artifact_parsers as ap
import clad_stages as cs


def concepts(feature_root: str) -> List[Dict]:
    concept_dir = cs.CONCEPT_DIR(feature_root)
    out = []
    if os.path.isdir(concept_dir):
        for fname in sorted(os.listdir(concept_dir)):
            if not fname.endswith(".concept.md"):
                continue
            c = ap.parse_concept(os.path.join(concept_dir, fname))
            if c.name == "Web":
                continue
            rels = ap.parse_state_relations(c.state_lines)
            out.append({
                "name": c.name,
                "actions": [a.name for a in c.actions],
                "fields": [r.field for r in rels],
            })
    return out


def scenarios(feature_root: str) -> List[str]:
    usecase = os.path.join(feature_root, "stages", "01_usecase", "output",
                           "usecase.md")
    if not os.path.isfile(usecase):
        return []
    return sorted(ap.parse_scenario_names(usecase))


def syncs(feature_root: str) -> List[Dict]:
    out = []
    for s in ap.parse_syncs(cs.SYNC_DIR(feature_root)):
        out.append({
            "name": s.name,
            "triggerConcept": s.trigger_concept,
            "triggerAction": s.trigger_action,
            "triggerOutcome": s.trigger_outcome,
            "then": [{"concept": c, "action": a} for c, a in s.then_targets],
        })
    return out


def chain_actions(feature_root: str) -> Dict[str, List[str]]:
    """Scenario slug -> the ordered `Concept.action` token chain (the Then column
    of each canonical per-scenario chain table). Terminal `Web.respond[NNN]` rows
    are included as `Web.respond` (suffix stripped) so a runtime can reconstruct
    the full step-definition token sequence."""
    chain_dir = cs.CHAIN_DIR(feature_root)
    out: Dict[str, List[str]] = {}
    if not os.path.isdir(chain_dir):
        return out
    for fname in sorted(os.listdir(chain_dir)):
        if not fname.endswith("-chain.md") or fname.endswith("-all-scenarios-chain.md"):
            continue
        scenario = fname.replace("-chain.md", "")
        rows = ap.parse_chain_table(os.path.join(chain_dir, fname))
        out[scenario] = [f"{r.then_concept}.{r.then_action}" for r in rows]
    return out


def action_outcomes(feature_root: str) -> Dict[str, List[str]]:
    """`Concept.action` -> the distinct outcome tokens (base names) it emits across
    all canonical chain tables. Deduplicated, first-seen order preserved."""
    chain_dir = cs.CHAIN_DIR(feature_root)
    out: Dict[str, List[str]] = {}
    if not os.path.isdir(chain_dir):
        return out
    for fname in sorted(os.listdir(chain_dir)):
        if not fname.endswith("-chain.md") or fname.endswith("-all-scenarios-chain.md"):
            continue
        for r in ap.parse_chain_table(os.path.join(chain_dir, fname)):
            key = f"{r.then_concept}.{r.then_action}"
            if not r.outcome_base:
                continue
            vals = out.setdefault(key, [])
            if r.outcome_base not in vals:
                vals.append(r.outcome_base)
    return out


def expected_outputs(feature_root: str) -> Dict[str, List[str]]:
    """Map stage id -> the artefact filenames that stage is expected to produce."""
    out: Dict[str, List[str]] = {}

    out["02_concepts"] = [c["name"] + ".concept.md" for c in concepts(feature_root)]
    out["03_syncs"] = [s["name"] + ".sync.md" for s in syncs(feature_root)]
    out["03a_dependency-review"] = [
        c["name"] + "-card.md" for c in concepts(feature_root)] + ["pattern-d-summary.md"]
    out["03b_data-model"] = [c["name"] + ".data-model.md" for c in concepts(feature_root)]
    out["04_implement/04b_spec"] = [c["name"] + ".spec.md" for c in concepts(feature_root)]

    chain_dir = cs.CHAIN_DIR(feature_root)
    chain_files = []
    if os.path.isdir(chain_dir):
        chain_files = sorted(
            f for f in os.listdir(chain_dir)
            if f.endswith("-chain.md") and not f.endswith("-all-scenarios-chain.md"))
    out["01b_chain-table"] = chain_files

    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Emit a JSON descriptor of a CLAD feature")
    parser.add_argument("--feature", required=True, help="Feature root path")
    args = parser.parse_args()

    feature_root = os.path.abspath(args.feature)
    if not os.path.isdir(feature_root):
        print(json.dumps({"error": f"feature root not found: {feature_root}"}))
        sys.exit(1)

    descriptor = {
        "feature": os.path.basename(feature_root.rstrip("/")),
        "concepts": concepts(feature_root),
        "scenarios": scenarios(feature_root),
        "syncs": syncs(feature_root),
        "chainActions": chain_actions(feature_root),
        "actionOutcomes": action_outcomes(feature_root),
        "expectedOutputs": expected_outputs(feature_root),
    }
    print(json.dumps(descriptor, indent=2))


if __name__ == "__main__":
    main()
