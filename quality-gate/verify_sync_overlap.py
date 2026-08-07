#!/usr/bin/env python3
"""
verify_sync_overlap.py — detects overlapping sync operations (deadlock risk).

Why this exists:
    When two syncs touch the same set of concepts, and those syncs fire
    under concurrency, they can deadlock if they acquire concept locks in
    different orders. This is invisible at design review unless you
    explicitly check for overlapping concept sets across syncs.

    In Axiomatic Design terms: a fully-populated sub-matrix of syncs
    touching the same concepts is a "coupled matrix" — both syncs depend
    on both concepts, creating a potential circular dependency at runtime.

Checks:
    1. For each pair of syncs, computes the set of concepts each touches.
    2. If two syncs share 2+ concepts, flags the overlap.
    3. Reports every overlapping pair with the shared concepts.

Usage:
    python3 verify_sync_overlap.py --sync-dir <path-to-03_syncs/output>
"""

import argparse
import os
import re
import sys
from collections import defaultdict


_WHEN_CONCEPT_RE = re.compile(r'(\w+)/\w+\s*:', re.MULTILINE)
_THEN_CONCEPT_RE = re.compile(r'(\w+)/\w+\s*:', re.MULTILINE)


def extract_concepts(text):
    """Extract unique concept names from sync text."""
    concepts = set()
    when_block = text.partition('when {')[2].partition('}')[0] if 'when {' in text else ''
    then_block = text.partition('then {')[2].partition('}')[0] if 'then {' in text else ''
    concepts.update(_WHEN_CONCEPT_RE.findall(when_block))
    concepts.update(_THEN_CONCEPT_RE.findall(then_block))
    return concepts


def parse_syncs(sync_dir):
    """Return dict of sync_name → set of concept names."""
    syncs = {}
    for fname in sorted(os.listdir(sync_dir)):
        if not fname.endswith('.sync.md'):
            continue
        path = os.path.join(sync_dir, fname)
        with open(path) as fh:
            text = fh.read()
        name = fname.replace('.sync.md', '')
        concepts = extract_concepts(text)
        if concepts:
            syncs[name] = concepts
    return syncs


def main():
    parser = argparse.ArgumentParser(
        description="Detect overlapping sync operations (deadlock risk)")
    parser.add_argument("--sync-dir", required=True,
                        help="Path to 03_syncs/output/")
    args = parser.parse_args()

    if not os.path.isdir(args.sync_dir):
        print(f"FAIL  sync directory not found: {args.sync_dir}")
        sys.exit(1)

    syncs = parse_syncs(args.sync_dir)
    if len(syncs) < 2:
        print("PASS  fewer than 2 syncs — nothing to overlap")
        sys.exit(0)

    overlaps = []
    names = sorted(syncs.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            # Exclude Web — it's the bootstrap concept, naturally shared
            a = syncs[names[i]] - {'Web'}
            b = syncs[names[j]] - {'Web'}
            shared = a & b
            if len(shared) >= 2:
                overlaps.append((names[i], names[j], shared))

    if overlaps:
        print(f"WARN  {len(overlaps)} sync pair(s) share 2+ concepts"
              f" (potential deadlock risk):\n")
        for s1, s2, shared in overlaps:
            shared_str = ", ".join(sorted(shared))
            print(f"  {s1}  ⇄  {s2}")
            print(f"    shared concepts: {shared_str}")
            print(f"    risk: concurrent execution may acquire locks in"
                  f" different orders → deadlock")
            print(f"    fix: ensure both syncs lock concepts in the same"
                  f" order (e.g. {sorted(shared)[0]} before"
                  f" {sorted(shared)[1]})")
            print()
        sys.exit(1)
    else:
        print(f"PASS  no overlapping sync pairs across {len(syncs)} syncs")
        sys.exit(0)


if __name__ == "__main__":
    main()
