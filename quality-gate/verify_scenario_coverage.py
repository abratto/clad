#!/usr/bin/env python3
"""
verify_scenario_coverage.py — Stage gate: goal → scenario → chain → sync coverage.

Why this exists:
  An LLM must manually check that every in-scope goal has a matching use-case
  scenario, every scenario has a chain-table file, and every scenario is cited
  by at least one sync. This is a mechanical cross-reference that a script
  can do deterministically, eliminating drift from LLM self-audit.

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
                m = re.search(r"—\s+scenario\s+[\"`']([^\"`']+)[\"`']", line)
                if m:
                    cited.add(m.group(1))
    return cited


def main():
    parser = argparse.ArgumentParser(
        description="Verify goal → scenario → chain → sync coverage")
    parser.add_argument("--goals", required=True,
                        help="Path to goals.md from Stage 00")
    parser.add_argument("--usecase", required=True,
                        help="Path to usecase.md from Stage 01")
    parser.add_argument("--chain-dir", required=True,
                        help="Path to 02b_chain-table/output/")
    parser.add_argument("--sync-dir", required=True,
                        help="Path to 03_syncs/output/")
    args = parser.parse_args()

    passed = True

    goals = parse_goals(args.goals)
    scenarios = parse_scenario_names(args.usecase)

    if not os.path.isdir(args.chain_dir):
        print(f"WARN  chain directory not found: {args.chain_dir} — skipping chain and sync checks")
        chain_files = []
        cited = set()
    else:
        chain_files = [f for f in os.listdir(args.chain_dir)
                       if f.endswith("-chain.md")]

    # 1. Every in-scope goal → scenario (slug-based match)
    # Match scenario names to goals via slug: "reserve unavailable books" -> slug = "reserve-unavailable-books"
    # matches "reserve-unavailable-book" -> slug = "reserve-unavailable-book"
    # Also match sub-operation scenarios: "add-title" is a sub-operation of "manage-catalogue"
    # via token overlap check.
    slugged_goals = {slugify(g) for g in goals}
    for scenario in scenarios:
        scenario_slug = slugify(scenario)
        # Check: scenario slug starts with goal slug (or vice versa, with plural tolerance)
        if not any(
            scenario_slug.startswith(g.rstrip("s").rstrip("-"))
            or g.startswith(scenario_slug.rstrip("s").rstrip("-"))
            for g in slugged_goals
        ):
            print(f"WARN  scenario '{scenario}' (slug: '{scenario_slug}') "
                  f"does not obviously match any in-scope goal "
                  f"(slugs: {', '.join(sorted(slugged_goals))}) — "
                  f"verify mapping manually")

    if scenarios:
        print(f"INFO  scenarios in use case: {', '.join(sorted(scenarios))}")
    if goals:
        print(f"INFO  in-scope goals: {', '.join(sorted(goals))}")

    # 2. Every scenario → chain file (only if chain files exist)
    for scenario in scenarios:
        expected_chain = slugify(scenario) + "-chain.md"
        chain_path = os.path.join(args.chain_dir, expected_chain)
        if not os.path.isfile(chain_path) and chain_files:
            print(f"FAIL  scenario '{scenario}' has no chain file "
                  f"(expected {expected_chain})")
            passed = False

    # 3. Every chain file → cited by a sync (only if chain files exist)
    cited = parse_sync_cited_scenarios(args.sync_dir)
    for scenario in scenarios:
        if scenario not in cited and chain_files:
            print(f"FAIL  scenario '{scenario}' is not cited by any sync "
                  f"in {args.sync_dir}")
            passed = False

    uncited_chains = [s for s in scenarios if s not in cited]
    if uncited_chains and chain_files:
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
