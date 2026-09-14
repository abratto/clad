#!/usr/bin/env python3
"""
verify_sync_route_filters.py — R11: route scoping on shared-trigger syncs.

A sync that fires on a business-concept action (not the `Web` bootstrap) and
writes `Web/respond` can collide with another route that produces the same
trigger. This check warns (never blocks) when two or more `SyncRule.of` rules share a trigger
and none carries a route guard (`?route`) or a `when`-clause input matcher
(`Map.of("route", lit(...))` — R15 matcher form)
share the same `(concept, action, outcome)` trigger and none carries a `?route`
guard — positive evidence of the R11 hazard.

Canonical-profile enforcement is advisory by design: the shipped examples have
no cross-route collision, and a blocking rule needs an engine
route-propagation decision. The legacy `SyncTrigger`/SPARQL profile was
retired (see `reference-impl/LEGACY.md`).

Usage:
  python3 verify_sync_route_filters.py --sync-impl-dir <path>

Exit: always 0 (advisory).
"""

import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


_SYNC_RULE_HEAD = re.compile(
    r'SyncRule\.of\(\s*"(\w+)"\s*,\s*"(\w+)"\s*,\s*"(\w+)"\s*,\s*"([^"]*)"')
_SYNC_RULE_RESPOND = re.compile(r'invoke\(\s*"Web"\s*,\s*"respond"')
_SYNC_RULE_ROUTE_GUARD = re.compile(r'(?:Clause\.)?(?:Guard|Bind)\(\s*"\?route"|Map\.of\(\s*"route"')


def scan_sync_rule_ambiguity(root):
    parsed = []
    for java_file in sorted(root.rglob("*.java")):
        text = java_file.read_text(encoding="utf-8", errors="replace")
        heads = list(_SYNC_RULE_HEAD.finditer(text))
        for index, m in enumerate(heads):
            start = m.start()
            end = heads[index + 1].start() if index + 1 < len(heads) else len(text)
            body = text[start:end]
            name, concept, action, outcome = m.groups()
            parsed.append((
                name, concept, action, outcome,
                bool(_SYNC_RULE_RESPOND.search(body)),
                bool(_SYNC_RULE_ROUTE_GUARD.search(body)),
            ))
    groups = defaultdict(list)
    for rule in parsed:
        _name, concept, _action, _outcome, writes, _guard = rule
        if concept != "Web" and writes:
            groups[(rule[1], rule[2], rule[3])].append(rule)
    warnings = []
    for (concept, action, outcome), rules in groups.items():
        if len(rules) > 1 and not any(r[5] for r in rules):
            names = ", ".join(r[0] for r in rules)
            warnings.append(
                f"R11: {len(rules)} syncs share trigger "
                f"{concept}/{action}[{outcome}] and write Web/respond with no "
                f"route guard: {names}")
    return warnings, len(parsed)


def main():
    parser = argparse.ArgumentParser(
        description="Advisory R11 route-scoping check for SyncRule syncs")
    parser.add_argument("--sync-impl-dir", default="",
                        help="Directory containing SyncRule Java implementations")
    args = parser.parse_args()

    if not args.sync_impl_dir or not os.path.isdir(args.sync_impl_dir):
        print(f"SKIP  sync implementation dir not found: {args.sync_impl_dir or '<unset>'}")
        sys.exit(0)

    warnings, parsed_rules = scan_sync_rule_ambiguity(Path(args.sync_impl_dir))
    for warning in warnings:
        print(f"WARN  {warning}")
    if warnings:
        print(f"WARN  R11 route scoping: {len(warnings)} ambiguous SyncRule "
              f"trigger(s); add a ?route guard or review Stage 03a.")
    else:
        print(f"PASS  R11 route scoping: {parsed_rules} SyncRule(s) examined, "
              f"no ambiguous shared-trigger respond sync.")
    sys.exit(0)


if __name__ == "__main__":
    main()
