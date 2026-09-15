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

from artifact_parsers import extract_block


_WHEN_CONCEPT_RE = re.compile(r'(\w+)/\w+\s*:', re.MULTILINE)
_THEN_CONCEPT_RE = re.compile(r'(\w+)/\w+\s*:', re.MULTILINE)


def extract_concepts(text):
    """Extract unique concept names from sync text.

    The `when` block may hold a multi-`when` join (all conjunct sources are
    touched); brace matching keeps nested `collect`-clause braces in `where`
    from truncating the scan.
    """
    concepts = set()
    when_block = extract_block(text, 'when')
    then_block = extract_block(text, 'then')
    concepts.update(_WHEN_CONCEPT_RE.findall(when_block))
    concepts.update(_THEN_CONCEPT_RE.findall(then_block))
    return concepts


def extract_concept_order(text):
    """Extract concept acquisition order from sync text.
    Returns ordered list of unique concepts as they appear in when→then."""
    when_block = extract_block(text, 'when')
    then_block = extract_block(text, 'then')
    seen = set()
    order = []
    for m in _WHEN_CONCEPT_RE.finditer(when_block):
        c = m.group(1)
        if c not in seen:
            seen.add(c)
            order.append(c)
    for m in _THEN_CONCEPT_RE.finditer(then_block):
        c = m.group(1)
        if c not in seen:
            seen.add(c)
            order.append(c)
    return order


def _sync_signature(path):
    """Read the sync's when/where literal assignments (route signature)."""
    with open(path) as fh:
        text = fh.read()
    when_block = extract_block(text, 'when')
    where_block = extract_block(text, 'where')
    lits = set()
    for clause in (when_block, where_block):
        lits |= set(re.findall(r"([\w]+)\s*=\s*([\"'])([^\"']*)\2", clause))
    return tuple(sorted(f"{a}={c}" for a, _q, c in lits))


def parse_syncs_with_signatures(sync_dir):
    """(concept_sets, concept_orders, literal signatures) keyed by sync name."""
    syncs = {}
    orders = {}
    signs = {}
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
            orders[name] = extract_concept_order(text)
            signs[name] = _sync_signature(path)
    return syncs, orders, signs


def main():
    parser = argparse.ArgumentParser(
        description="Detect overlapping sync operations (deadlock risk)")
    parser.add_argument("--sync-dir", required=True,
                        help="Path to 03_syncs/output/")
    parser.add_argument("--advisory", action="store_true",
                        help="Report findings as warnings instead of blocking")
    args = parser.parse_args()

    if not os.path.isdir(args.sync_dir):
        print(f"FAIL  sync directory not found: {args.sync_dir}")
        sys.exit(1)

    syncs, orders, signs = parse_syncs_with_signatures(args.sync_dir)
    if len(syncs) < 2:
        print("PASS  fewer than 2 syncs — nothing to overlap")
        sys.exit(0)

    blocking = []
    advisory = []
    names = sorted(syncs.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            # Exclude Web — it's the bootstrap concept, naturally shared
            a = syncs[names[i]] - {'Web'}
            b = syncs[names[j]] - {'Web'}
            shared = a & b
            if len(shared) >= 2:
                # Check lock ordering: do the shared concepts appear in
                # the same sequence in both syncs?
                sig_i, sig_j = signs.get(names[i], ()), signs.get(names[j], ())
                if sig_i and sig_j and sig_i != sig_j:
                    continue  # route-scoped away: matched literals differ
                order_a = [c for c in orders[names[i]] if c in shared]
                order_b = [c for c in orders[names[j]] if c in shared]
                if order_a == order_b:
                    advisory.append((names[i], names[j], shared,
                                     orders[names[i]]))
                else:
                    blocking.append((names[i], names[j], shared,
                                     orders[names[i]], orders[names[j]]))

    if blocking or advisory:
        if blocking:
            print(f"FAIL  {len(blocking)} sync pair(s) with conflicting lock"
                  f" orders (deadlock risk):\n")
            for s1, s2, shared, o1, o2 in blocking:
                shared_str = ", ".join(sorted(shared))
                print(f"  {s1}  ⇄  {s2}")
                print(f"    shared concepts: {shared_str}")
                print(f"    lock order: {s1}: {o1}  vs  {s2}: {o2}")
                print(f"    risk: concurrent execution may acquire locks in"
                      f" different orders → deadlock")
                print()

        if advisory:
            print(f"WARN  {len(advisory)} sync pair(s) share concepts but"
                  f" lock in same order (safe, advisory):\n")
            for s1, s2, shared, order in advisory:
                shared_str = ", ".join(sorted(shared))
                print(f"  {s1}  ⇄  {s2}")
                print(f"    shared concepts: {shared_str}")
                print(f"    lock order (same): {order}")
                print(f"    safe: both syncs acquire locks in the same"
                      f" sequence — no deadlock risk")
                print()

        if blocking:
            print("  Sync pairs with conflicting lock orders must be fixed.")
            print("  Ensure shared concepts are acquired in the same order"
                  " across all syncs.")
            sys.exit(0 if args.advisory else 1)
        else:
            print("  Ship-by: all overlapping syncs share the same lock order"
                  " — deadlock prevented by design.")
            sys.exit(0)
    else:
        print(f"PASS  no overlapping sync pairs across {len(syncs)} syncs")
        sys.exit(0)


if __name__ == "__main__":
    main()
