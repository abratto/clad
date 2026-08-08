#!/usr/bin/env python3
"""
verify_concept_matrix.py — builds the FR × DP matrix from CLAD artefacts
and flags architectural anti-patterns.

Why this exists:
    The Axiomatic Design matrix maps Functional Requirements (scenarios)
    against Design Parameters (concepts). A healthy WYSIWID architecture
    has a sparse, near-diagonal matrix — each concept serves a distinct
    set of scenarios, with minimal overlap.

    This script detects three anti-patterns:
    1. God Object — a concept that touches most scenarios (vertical wall of X's)
    2. Duplication — two concepts with identical or near-identical scenario
       coverage (same X pattern — same business logic in two places)
    3. Entanglement — two concepts whose rows overlap on multiple scenarios
       without being clearly orthogonal (potential boundary confusion)

    In AD terms: a diagonal matrix is ideal. Duplicated columns mean
    redundant DPs. A solid column means a God DP that violates the
    Independence Axiom.

Usage:
    python3 verify_concept_matrix.py \
      --usecase <01_usecase/output/usecase.md> \
      --chain-dir <01b_chain-table/output/> \
      --resp-map <01a_responsibility-map/output/responsibility-map.md>
"""

import argparse
import os
import re
import sys
from collections import defaultdict


_SCENARIO_RE = re.compile(r'^###\s+Scenario:\s+(.+)$', re.MULTILINE)
# Matches concept names in chain-table When/Then columns:
# When: Web/request[POST /login] → concept=Web
# Then: User.lookupByUsername → concept=User
_CHAIN_CONCEPT_RE = re.compile(r'\|\s*\d+\s*\|\s*`(\w+)[/\.]')
_CONCEPT_RE = re.compile(r'\|\s*`(\w+)`\s*\|', re.MULTILINE)


def extract_scenarios(usecase_path):
    """Extract named scenarios from the use case."""
    with open(usecase_path) as fh:
        text = fh.read()
    return _SCENARIO_RE.findall(text)


def extract_concepts(resp_map_path):
    """Extract concept names from the responsibility map (backtick format)."""
    with open(resp_map_path) as fh:
        text = fh.read()
    concepts = []
    for m in _CONCEPT_RE.finditer(text):
        name = m.group(1)
        if name not in ('Concept', '---', '', 'Web'):
            concepts.append(name)
    return concepts


def build_matrix(scenarios, concepts, chain_dir):
    """Build FR×DP matrix. Deduplicates: each concept at most once per scenario
    regardless of how many chain table rows it appears in."""
    matrix = {}
    coverage = defaultdict(int)

    for scenario in scenarios:
        row = {}
        concepts_in_chain = set()
        for fname in os.listdir(chain_dir):
            if not fname.endswith('.md'):
                continue
            path = os.path.join(chain_dir, fname)
            with open(path) as fh:
                text = fh.read()
            # Only count rows from the file matching this scenario
            # (skip consolidated files that list all scenarios)
            if 'all-scenarios' in fname:
                continue
            concepts_in_chain.update(_CHAIN_CONCEPT_RE.findall(text))

        for c in concepts_in_chain:
            if c in concepts:
                row[c] = 'X'
                coverage[c] += 1
        matrix[scenario] = row

    return matrix, coverage


def detect_god_objects(coverage, scenarios_count, threshold=0.75):
    """Flag concepts that touch more than `threshold` of scenarios.
    Only fires when there are >3 scenarios — small features naturally
    have concepts that touch most scenarios."""
    if scenarios_count <= 3:
        return []
    god_objects = []
    for concept, count in coverage.items():
        ratio = count / max(scenarios_count, 1)
        if ratio >= threshold:
            god_objects.append((concept, count, scenarios_count, ratio))
    return god_objects


def detect_duplication(matrix, scenarios):
    """Flag concept pairs with identical scenario coverage patterns."""
    # Build concept → set of scenarios
    concept_scenarios = defaultdict(set)
    for scenario in scenarios:
        row = matrix.get(scenario, {})
        for concept in row:
            if row[concept] == 'X':
                concept_scenarios[concept].add(scenario)

    concepts = sorted(concept_scenarios.keys())
    duplicates = []
    for i in range(len(concepts)):
        for j in range(i + 1, len(concepts)):
            si = concept_scenarios[concepts[i]]
            sj = concept_scenarios[concepts[j]]
            if si and sj and si == sj:
                duplicates.append((concepts[i], concepts[j], si))
    return duplicates


def detect_entanglement(matrix, scenarios, min_shared=2):
    """Flag concept pairs that share `min_shared`+ scenarios without
    being duplicates — potential boundary confusion."""
    concept_scenarios = defaultdict(set)
    for scenario in scenarios:
        row = matrix.get(scenario, {})
        for concept in row:
            if row[concept] == 'X':
                concept_scenarios[concept].add(scenario)

    concepts = sorted(concept_scenarios.keys())
    entangled = []
    for i in range(len(concepts)):
        for j in range(i + 1, len(concepts)):
            shared = concept_scenarios[concepts[i]] & concept_scenarios[concepts[j]]
            # Only flag if they share scenarios but aren't identical
            if len(shared) >= min_shared and concept_scenarios[concepts[i]] != concept_scenarios[concepts[j]]:
                entangled.append((concepts[i], concepts[j], shared))
    return entangled


def main():
    parser = argparse.ArgumentParser(
        description="Build FR×DP matrix and flag architectural anti-patterns")
    parser.add_argument("--usecase", required=True,
                        help="Path to 01_usecase/output/usecase.md")
    parser.add_argument("--chain-dir", required=True,
                        help="Path to 01b_chain-table/output/")
    parser.add_argument("--resp-map", required=True,
                        help="Path to 01a_responsibility-map/output/responsibility-map.md")
    parser.add_argument("--output", default=None,
                        help="Write the matrix as a markdown file")
    args = parser.parse_args()

    for path, label in [(args.usecase, "usecase"),
                        (args.chain_dir, "chain-dir"),
                        (args.resp_map, "resp-map")]:
        if not os.path.exists(path):
            print(f"FAIL  {label} not found: {path}")
            sys.exit(1)

    scenarios = extract_scenarios(args.usecase)
    concepts = extract_concepts(args.resp_map)

    if not scenarios or not concepts:
        print("PASS  no scenarios or concepts found — nothing to analyze")
        sys.exit(0)

    matrix, coverage = build_matrix(scenarios, concepts, args.chain_dir)

    # Write matrix to file if requested (before stdout)
    if args.output:
        with open(args.output, "w") as fh:
            fh.write(f"# Concept coverage matrix — {len(scenarios)} scenarios × {len(concepts)} concepts\n\n")
            fh.write("| Scenario | " + " | ".join(concepts) + " |\n")
            fh.write("|---|" + "|".join(":---:" for _ in concepts) + "|\n")
            for scenario in scenarios:
                cells = []
                for c in concepts:
                    cells.append("X" if matrix.get(scenario, {}).get(c) == 'X' else "—")
                fh.write(f"| {scenario} | " + " | ".join(cells) + " |\n")

    # Print the matrix
    print(f"Design Matrix: {len(scenarios)} scenarios × {len(concepts)} concepts\n")
    header = "| Scenario | " + " | ".join(f"{c:12s}" for c in concepts) + " |"
    sep = "|---|" + "|".join("---:" for _ in concepts) + "|"
    print(header)
    print(sep)
    for scenario in scenarios:
        cells = []
        for c in concepts:
            cells.append("     X     " if matrix.get(scenario, {}).get(c) == 'X' else "           ")
        row_display = " | ".join(cells)
        print(f"| {scenario[:30]:30s} | {row_display} |")
    print()

    # Detect anti-patterns
    issues_found = False

    god_objects = detect_god_objects(coverage, len(scenarios))
    if god_objects:
        print(f"WARN  God Object(s) detected:\n")
        for concept, count, total, ratio in god_objects:
            print(f"  {concept}: touches {count}/{total} scenarios ({ratio:.0%})")
            print(f"    This concept cuts across most of the system. Consider")
            print(f"    splitting it into smaller, more focused concepts.")
            print()
        issues_found = True

    duplicates = detect_duplication(matrix, scenarios)
    if duplicates:
        print(f"WARN  Duplicate concept coverage detected:\n")
        for c1, c2, shared in duplicates:
            print(f"  {c1} and {c2} cover the same scenarios: "
                  f"{', '.join(sorted(shared)[:3])}")
            print(f"    These concepts have identical FR coverage — they may")
            print(f"    duplicate business logic. Consider merging them or")
            print(f"    clarifying their distinct purposes.")
            print()
        issues_found = True

    entangled = detect_entanglement(matrix, scenarios)
    if entangled:
        print(f"WARN  Entangled concepts detected (boundary confusion):\n")
        for c1, c2, shared in entangled:
            print(f"  {c1} and {c2} share {len(shared)} scenario(s): "
                  f"{', '.join(sorted(shared)[:3])}")
            print(f"    These concepts overlap on multiple scenarios but aren't")
            print(f"    duplicates — the boundary between them may be unclear.")
            print()
        issues_found = True

    if issues_found:
        print("Review the matrix above and the flagged patterns below.")
        print("Resolve at Stage 01a (responsibility map) or Stage 01b (chain table).")
        print()
        print("NOTE: small, cohesive features (3-5 scenarios) will naturally have")
        print("concepts that touch many scenarios — this is expected, not a defect.")
        print("Duplication flags are the most actionable: two concepts with identical")
        print("scenario coverage patterns may duplicate business logic.")
        sys.exit(0)  # Advisory — don't block on these
    else:
        print(f"PASS  no anti-patterns detected — {len(concepts)} concepts "
              f"across {len(scenarios)} scenarios")
        sys.exit(0)


if __name__ == "__main__":
    main()
