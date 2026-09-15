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
import sys
from collections import defaultdict

from artifact_parsers import Conjunct, parse_syncs


def parse_syncs_edges(sync_dir):
    """Parse all .sync.md files and return list of routing edges.

    Edge identity is route-scoped: (sync_name, source_node, target_node),
    where source_node is the trigger route identity
    (concept, action, completion-token-verbatim). Two invocation positions
    that differ solely by a matched literal / outcome payload (R15's
    `check = entry | application` device, conduit rebuild experiment) are
    therefore DISTINCT nodes and cannot constitute a false cycle through
    the same concept.

    A joined (multi-`when`) rule contributes an incoming edge from **every**
    conjunct's source, not only the primary — the rule can fire only when all
    conjuncts completed, so each is a real dependency.
    """
    edges = []
    for s in parse_syncs(sync_dir):
        sign = "+".join(s.route_literals or ())
        sources = s.conjuncts or [
            Conjunct(None, s.trigger_concept, s.trigger_action, s.trigger_outcome)]
        for c in sources:
            src = (c.concept, c.action, (c.outcome or "").strip(), sign)
            for concept, action in s.then_targets:
                edges.append((s.name, src, (concept, action, "", sign)))
    return edges


def build_graph(edges):
    """Build adjacency list from concept→concept edges.
    Excludes the Web bootstrap concept — it naturally appears at both
    ends of chains (entry and exit) and doesn't constitute a cycle."""
    def node_concept(node):
        return node[0]

    graph = defaultdict(set)
    for _sync_name, src, tgt in edges:
        if node_concept(src) == "Web" or node_concept(tgt) == "Web":
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

    edges = parse_syncs_edges(args.sync_dir)
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
              f"in {len(set(k[0] for k in graph))} concepts")
        sys.exit(0)


if __name__ == "__main__":
    main()
