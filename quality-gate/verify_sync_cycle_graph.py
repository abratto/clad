#!/usr/bin/env python3
"""
verify_sync_cycle_graph.py — detects design-time sync cycles (A→B→A).

Why this exists:
    The WYSIWID dedup guard catches runtime infinite loops (FILTER NOT EXISTS
    { ?_when_1 :syncName [] }), but it can't detect design-time cycles. If
    Sync A fires on Concept X and invokes Concept Y, and Sync B fires on
    Concept Y and invokes Concept X, the system has a cycle that the dedup
    guard will catch at runtime — but a human should catch it at Stage 03
    review. This script makes that detection deterministic.

    In Axiomatic Design terms: a diagonal matrix is ideal. A cycle means
    the matrix has off-diagonal X's that form a loop, violating the
    Independence Axiom.

Checks:
    1. Builds a directed graph from syncs (when: ConceptA → then: ConceptB).
    2. Detects cycles in the graph.
    3. Reports every cycle found.

Usage:
    python3 verify_sync_cycle_graph.py --sync-dir <path-to-03_syncs/output>
"""

import argparse
import os
import re
import sys
from collections import defaultdict


_SYNC_NAME_RE = re.compile(r'^sync\s+(\w+)', re.MULTILINE)
_WHEN_CONCEPT_RE = re.compile(r'(\w+)/\w+\s*:', re.MULTILINE)
_THEN_CONCEPT_RE = re.compile(r'(\w+)/\w+\s*:', re.MULTILINE)


def parse_syncs(sync_dir):
    """Parse all .sync.md files and return list of (sync_name, from_concept, to_concept) edges."""
    edges = []
    for fname in sorted(os.listdir(sync_dir)):
        if not fname.endswith('.sync.md'):
            continue
        path = os.path.join(sync_dir, fname)
        with open(path) as fh:
            text = fh.read()

        sync_name = fname.replace('.sync.md', '')

        # Find concept names in the when/then clauses
        # Partition on "when {" and "then {" blocks
        when_block = text.partition('when {')[2].partition('}')[0] if 'when {' in text else ''
        then_block = text.partition('then {')[2].partition('}')[0] if 'then {' in text else ''

        from_concepts = _WHEN_CONCEPT_RE.findall(when_block)
        to_concepts = _THEN_CONCEPT_RE.findall(then_block)

        for fc in from_concepts:
            for tc in to_concepts:
                edges.append((sync_name, fc, tc))

    return edges


def build_graph(edges):
    """Build adjacency list from concept→concept edges.
    Excludes the Web bootstrap concept — it naturally appears at both
    ends of chains (entry and exit) and doesn't constitute a cycle."""
    graph = defaultdict(set)
    for _sync_name, src, tgt in edges:
        if src == 'Web' or tgt == 'Web' or src == tgt:
            continue
        graph[src].add(tgt)
    return graph


def find_cycles(graph):
    """Find all cycles in the directed graph using DFS."""
    cycles = []
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}
    parent = {}
    path = []

    def dfs(node):
        color[node] = GRAY
        path.append(node)
        for neighbor in graph.get(node, set()):
            if color.get(neighbor, WHITE) == GRAY:
                # Found a cycle — extract the path from neighbor to node
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)
            elif color.get(neighbor, WHITE) == WHITE:
                parent[neighbor] = node
                dfs(neighbor)
        path.pop()
        color[node] = BLACK

    for node in list(graph.keys()):
        if color.get(node, WHITE) == WHITE:
            dfs(node)

    return cycles


def main():
    parser = argparse.ArgumentParser(
        description="Detect design-time sync cycles (A→B→A)")
    parser.add_argument("--sync-dir", required=True,
                        help="Path to 03_syncs/output/")
    parser.add_argument("--advisory", action="store_true",
                        help="Report findings as warnings instead of blocking")
    args = parser.parse_args()

    if not os.path.isdir(args.sync_dir):
        print(f"FAIL  sync directory not found: {args.sync_dir}")
        sys.exit(1)

    edges = parse_syncs(args.sync_dir)
    if not edges:
        print("PASS  no syncs found — nothing to check")
        sys.exit(0)

    graph = build_graph(edges)
    cycles = find_cycles(graph)

    if cycles:
        label = "WARN " if args.advisory else "FAIL "
        print(f"{label} {len(cycles)} design-time sync cycle(s) detected:\n")
        for i, cycle in enumerate(cycles):
            path_str = " → ".join(cycle)
            print(f"  Cycle {i + 1}: {path_str}")
        print()
        print("  Sync cycles mean two syncs chain back onto each other. This")
        print("  creates an infinite loop that the dedup guard catches at runtime")
        print("  but that should be caught at design time. Split the concepts or")
        print("  add an intermediate concept to break the loop.")
        sys.exit(0 if args.advisory else 1)
    else:
        print(f"PASS  no sync cycles detected across {len(edges)} edges "
              f"in {len(graph)} concepts")
        sys.exit(0)


if __name__ == "__main__":
    main()
