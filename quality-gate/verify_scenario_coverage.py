#!/usr/bin/env python3
"""
verify_scenario_coverage.py — Stage gate: goal → scenario → chain → sync coverage.

Checks:
  1. Every in-scope goal in goals.md maps to a ### Scenario: heading in usecase.md
  2. Every ### Scenario: in usecase.md has a matching <name>-chain.md in the chain dir
  3. Every <name>-chain.md scenario is cited by at least one sync in the sync dir

Usage:
  python3 verify_scenario_coverage.py \
    --goals <goals.md> \
    --usecase <usecase.md> \
    --chain-dir <chain-output/> \
    --sync-dir <sync-output/>
"""

import argparse
import os
import re
import sys


def parse_goals(path):
    """Return set of in-scope goal phrases from the goals.md In scope table."""
    goals = set()
    with open(path) as f:
        lines = f.readlines()
    in_table = False
    for line in lines:
        # Detect table header row (| Actor | Goal | ...)
        if line.strip().startswith("| Actor | Goal |"):
            in_table = True
            continue
        if in_table:
            # Stop at the first blank line or ## heading after the table
            if line.strip() == "" or line.startswith("##"):
                in_table = False
                continue
            # Skip separator rows (|----|----|...)
            if re.match(r"^\|[\s\-:]+\|", line):
                continue
            # Parse data row: | Actor | Goal | ...
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                goals.add(parts[2])  # Goal column
    return goals


def parse_scenario_names(usecase_path):
    """Return set of scenario names from ### Scenario: headings."""
    names = set()
    with open(usecase_path) as f:
        for line in f:
            m = re.match(r"^### Scenario:\s+(.+)$", line.strip())
            if m:
                names.add(m.group(1).strip())
    return names


def slugify(name):
    """Convert a scenario name to the slug used in chain-table filenames."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s


def parse_sync_cited_scenarios(sync_dir):
    """Return set of scenario names cited across all sync files."""
    cited = set()
    if not os.path.isdir(sync_dir):
        return cited
    for fname in os.listdir(sync_dir):
        if not fname.endswith(".sync.md"):
            continue
        path = os.path.join(sync_dir, fname)
        with open(path) as f:
            for line in f:
                m = re.search(r"—\s+scenario\s+`([^`]+)`", line)
                if m:
                    cited.add(m.group(1))
    return cited


def main():
    parser = argparse.ArgumentParser(
        description="Verify goal → scenario → chain → sync coverage")
    parser.add_argument("--goals", required=True)
    parser.add_argument("--usecase", required=True)
    parser.add_argument("--chain-dir", required=True)
    parser.add_argument("--sync-dir", required=True)
    args = parser.parse_args()

    passed = True

    goals = parse_goals(args.goals)
    scenarios = parse_scenario_names(args.usecase)

    if not os.path.isdir(args.chain_dir):
        print(f"FAIL  chain directory not found: {args.chain_dir}")
        sys.exit(1)

    # 1. Every in-scope goal → scenario (count heuristic)
    # Semantic mapping requires human judgment — we check that the scenario
    # count is at least the goal count, which is necessary but not sufficient.
    if len(scenarios) < len(goals):
        print(f"FAIL  fewer scenarios ({len(scenarios)}) than in-scope "
              f"goals ({len(goals)}) — each goal needs at least one scenario")
        passed = False

    if scenarios:
        print(f"INFO  scenarios in use case: {', '.join(sorted(scenarios))}")
    if goals:
        print(f"INFO  in-scope goals: {', '.join(sorted(goals))}")

    # 2. Every scenario → chain file
    for scenario in scenarios:
        expected_chain = slugify(scenario) + "-chain.md"
        chain_path = os.path.join(args.chain_dir, expected_chain)
        if not os.path.isfile(chain_path):
            print(f"FAIL  scenario '{scenario}' has no chain file "
                  f"(expected {expected_chain})")
            passed = False

    # 3. Every chain file → cited by a sync
    chain_files = [f for f in os.listdir(args.chain_dir)
                   if f.endswith("-chain.md")]
    cited = parse_sync_cited_scenarios(args.sync_dir)
    for scenario in scenarios:
        if scenario not in cited:
            print(f"FAIL  scenario '{scenario}' is not cited by any sync "
                  f"in {args.sync_dir}")
            passed = False

    uncited_chains = [s for s in scenarios if s not in cited]
    if uncited_chains:
        print(f"INFO  scenarios not cited by syncs (Web-only failure paths?): "
              f"{', '.join(uncited_chains)}")

    if passed:
        print(f"PASS  scenario coverage: {len(goals)} goals → "
              f"{len(scenarios)} scenarios → {len(chain_files)} chain files → "
              f"{len(cited)} sync-cited scenarios")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
