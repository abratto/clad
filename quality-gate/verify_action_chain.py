#!/usr/bin/env python3
"""
verify_action_chain.py — Stage gate: action names flow consistently through
the full artefact chain: responsibility map → chain table → concept spec →
sync spec → dependency card → SPEC.

Why this exists:
  An action name can change in one artefact (e.g. a refactor in the chain table)
  without being updated downstream (concept spec, sync, card, SPEC). This script
  cross-references every Concept/action pair across all 6 artefact types and
  reports any that appear in one but not another. The chain tables are the
  reference — every action they invoke must appear everywhere downstream.

  The internal representation uses "/" as the separator (matching the paper's
  URI hierarchy scheme). Sync files use paper syntax (Concept/action:). Chain
  tables use dot notation (Concept.action) and are normalized on extraction.

Usage:
  python3 verify_action_chain.py \
    --resp-map <resp-map.md> \
    --chain-dir <chain-output/> \
    --concept-dir <concept-output/> \
    --sync-dir <sync-output/> \
    --dep-dir <dep-output/> \
    --spec-dir <spec-output/>
"""

import argparse
import os
import re
import sys


def parse_resp_map_actions(path):
    """Return set of Concept/action from the responsibility map's Owned actions column."""
    actions = set()
    with open(path) as f:
        in_table = False
        for line in f:
            if line.strip().startswith("| Concept | Owned state"):
                in_table = True
                continue
            if in_table:
                if re.match(r"^\|[\s\-:]+\|", line):
                    continue
                if not line.startswith("|"):
                    in_table = False
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4:
                    concept = parts[1].strip("`")
                    owned_actions = parts[3]
                    for a in re.findall(r"`([^`]+)`", owned_actions):
                        actions.add(f"{concept}/{a}")
    return actions


def parse_chain_table_actions(chain_dir):
    """Return set of Concept/action from chain-table Then columns (column 3).
    
    Chain tables use dot notation (Concept.action). This function normalises
    to slash notation (Concept/action) for internal cross-referencing.
    """
    actions = set()
    if not os.path.isdir(chain_dir):
        return actions
    for fname in os.listdir(chain_dir):
        if not fname.endswith("-chain.md"):
            continue
        with open(os.path.join(chain_dir, fname)) as f:
            for line in f:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) < 5:
                    continue
                # Skip header and separator rows
                if not parts[1].isdigit():
                    continue
                # Column index 3 (0-indexed) is the Then column
                then_col = parts[3]
                m = re.search(r"`([A-Za-z]+)\.([A-Za-z]+)", then_col)
                if m:
                    actions.add(f"{m.group(1)}/{m.group(2)}")
    return actions


def parse_concept_actions(concept_dir):
    """Return set of Concept/action from concept spec files."""
    actions = set()
    if not os.path.isdir(concept_dir):
        return actions
    for fname in os.listdir(concept_dir):
        if not fname.endswith(".concept.md"):
            continue
        concept = fname.replace(".concept.md", "")
        with open(os.path.join(concept_dir, fname)) as f:
            for line in f:
                m = re.match(r"^([a-z]\w+)\s+\[", line.strip())
                if m:
                    actions.add(f"{concept}/{m.group(1)}")
    return actions


def parse_sync_actions(sync_dir):
    """Return set of Concept/action from sync spec `then` clauses and sync Java files.
    
    Sync `.sync.md` files use paper block syntax:
        then {
            Concept/action: [ args ]
        }
    
    Java `@SyncMetadata` files use "Concept/action" directly.
    Both are normalised to Concept/action format.
    """
    actions = set()
    if not os.path.isdir(sync_dir):
        return actions

    for fname in os.listdir(sync_dir):
        filepath = os.path.join(sync_dir, fname)

        if fname.endswith(".sync.md"):
            with open(filepath) as f:
                in_then = False
                for line in f:
                    line_s = line.strip()
                    if line_s == "then {":
                        in_then = True
                        continue
                    if in_then:
                        if line_s == "}":
                            in_then = False
                            continue
                        m = re.search(r"([A-Za-z]+)/([A-Za-z]+):", line)
                        if m:
                            actions.add(f"{m.group(1)}/{m.group(2)}")

        elif fname.endswith(".java"):
            with open(filepath) as f:
                for line in f:
                    m = re.search(r'fires\s*=\s*"([A-Za-z]+)/([A-Za-z]+)', line)
                    if m:
                        actions.add(f"{m.group(1)}/{m.group(2)}")

    return actions


def parse_dep_card_actions(dep_dir):
    """Return set of Concept/action from dependency review cards."""
    actions = set()
    if not os.path.isdir(dep_dir):
        return actions
    for fname in os.listdir(dep_dir):
        if not fname.endswith("-card.md"):
            continue
        concept = fname.replace("-card.md", "")
        with open(os.path.join(dep_dir, fname)) as f:
            for line in f:
                # Card rows: | `<action>` | `<Sync>` | ...
                m = re.match(r"^\|\s*`(\w+)`\s*\|", line)
                if m:
                    actions.add(f"{concept}/{m.group(1)}")
    return actions


def parse_spec_actions(spec_dir):
    """Return set of Concept/action from SPEC files."""
    actions = set()
    if not os.path.isdir(spec_dir):
        return actions
    for fname in os.listdir(spec_dir):
        if not fname.endswith(".spec.md"):
            continue
        concept = fname.replace(".spec.md", "")
        with open(os.path.join(spec_dir, fname)) as f:
            for line in f:
                m = re.match(r"^###\s+`(\w+)\(", line.strip())
                if m:
                    actions.add(f"{concept}/{m.group(1)}")
    return actions


def main():
    parser = argparse.ArgumentParser(
        description="Verify action names flow consistently across all artefacts")
    parser.add_argument("--resp-map", required=True,
                        help="Path to 02a responsibility-map.md")
    parser.add_argument("--chain-dir", required=True,
                        help="Path to 02b_chain-table/output/")
    parser.add_argument("--concept-dir", required=True,
                        help="Path to 02_concepts/output/")
    parser.add_argument("--sync-dir", required=True,
                        help="Path to 03_syncs/output/ (spec files)")
    parser.add_argument("--dep-dir", required=True,
                        help="Path to 03a_dependency-review/output/")
    parser.add_argument("--spec-dir", required=True,
                        help="Path to 04b_spec/output/")
    args = parser.parse_args()

    sources = {
        "responsibility map":  parse_resp_map_actions(args.resp_map),
        "chain tables":        parse_chain_table_actions(args.chain_dir),
        "concept specs":       parse_concept_actions(args.concept_dir),
        "sync specs":          parse_sync_actions(args.sync_dir),
        "dep. cards":          parse_dep_card_actions(args.dep_dir),
        "SPECs":               parse_spec_actions(args.spec_dir),
    }

    # Filter out Web actions for all sources (Web is bootstrap)
    for name in sources:
        sources[name] = {a for a in sources[name] if not a.startswith("Web/")}

    if not any(sources.values()):
        print("FAIL  no actions parsed from any source")
        sys.exit(1)

    for name, actions in sources.items():
        print(f"INFO  {name}: {len(actions)} actions — {sorted(actions)}")

    # The chain tables are the reference for what the current feature
    # actually invokes. Every chained action must appear in all other
    # artefact types. Upstream artefacts (resp map, concept specs) may
    # declare extra actions not exercised by this UC — that is legal
    # (e.g. User.register, Session.lookup exist for future use cases).
    reference = sources["chain tables"]
    if not reference:
        reference = sources.get("sync specs", set())
    if not reference:
        print("FAIL  no reference actions (chain tables or sync specs)")
        sys.exit(1)

    passed = True
    for action in sorted(reference):
        missing_in = []
        for name, actions in sources.items():
            if name == "chain tables":
                continue
            if action not in actions:
                missing_in.append(name)
        if missing_in:
            print(f"FAIL  {action} (used in chain) missing from: "
                  f"{', '.join(missing_in)}")
            passed = False

    # Also check that responsibility map declares every chained action
    chained_not_in_resp = reference - sources["responsibility map"]
    if chained_not_in_resp:
        for a in sorted(chained_not_in_resp):
            print(f"FAIL  {a} used in chain but not declared in "
                  f"responsibility map")
        passed = False

    if passed:
        n = len(reference)
        total = sum(len(s) for s in sources.values())
        print(f"PASS  {n} chained actions flow consistently across "
              f"{len(sources)} artefact types ({total} total references)")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
