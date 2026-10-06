#!/usr/bin/env python3
"""
sync_information.py — advisory linter: each sync's A/B/C/D binding profile,
the feature aggregate, and two advisory findings.

Why this exists:
    SYNC_PATTERNS.md's A/B/C/D ladder is an information-content ladder
    (Suh's Information Axiom, adapted — see CITATIONS.md §Axiomatic Design):
    A (trigger token) adds zero information; B (flow-sibling output) adds
    chain-topology knowledge; C (sync constant) adds a copy point (every
    literal already lives in the chain row and the implementation); D
    (concept-state read) crosses the concept boundary — the only binding
    that does.

    The profile is read from each sync's own `## Where clause patterns (for
    Stage 03a audit)` table, so the labels are AUTHOR-DECLARED: this is a
    self-report, not a measurement. Misclassification (a literal that is
    secretly a function of the request, a hidden read) belongs to the
    literal-lock checks and Stage 03a, not to this profile.

Findings (advisory — always exit 0):
    * every D read: "outcome instead of read?" — concepts decide, syncs
      route; if the read decides something, the owning concept could emit an
      outcome the sync routes on (Pattern A) instead
    * join arity >= 3: three-plus conjuncts is real coordination knowledge
      in one rule; check the chain table intends it

Devil's advocate (adopted design): no weighted single score — pseudo-
quantitative and gameable. The vector is the report; the departures are
priced; only D and wide joins are flagged.

Usage:
  python3 sync_information.py --sync-dir <03_syncs/output/>
"""

import argparse
import os
import re
import sys

_PATTERN_ROW = re.compile(r"^\|\s*`([^`]*)`\s*\|\s*([ABCD])\S*\s*\|")
_CONJUNCT = re.compile(r"^\s*(?:[a-z][A-Za-z0-9]*:\s*)?[A-Z][A-Za-z0-9]*/[A-Za-z0-9]")
_WIDE_JOIN = 3


def parse_sync(path):
    """One sync's profile: (pattern counts, conjunct count, d_sources, has_table)."""
    counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    d_sources = []
    has_table = False
    in_when = False
    conjuncts = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if stripped.startswith("## Where clause patterns"):
                has_table = True
                continue
            if re.match(r"^when\s*\{", stripped):
                in_when = True
                continue
            if in_when:
                if stripped == "}":
                    in_when = False
                    continue
                if _CONJUNCT.match(line):
                    conjuncts += 1
                continue
            m = _PATTERN_ROW.match(stripped)
            if m:
                counts[m.group(2)] += 1
                if m.group(2) == "D":
                    d_sources.append(stripped)
    return counts, conjuncts, d_sources, has_table


def main():
    parser = argparse.ArgumentParser(
        description="Advisory: per-sync A/B/C/D binding profile + aggregate")
    parser.add_argument("--sync-dir", required=True,
                        help="Path to 03_syncs/output/")
    args = parser.parse_args()

    if not os.path.isdir(args.sync_dir):
        print(f"SKIP  no sync directory: {args.sync_dir}")
        return 0

    files = sorted(f for f in os.listdir(args.sync_dir) if f.endswith(".sync.md"))
    if not files:
        print(f"SKIP  no *.sync.md in {args.sync_dir}")
        return 0

    total = {"A": 0, "B": 0, "C": 0, "D": 0}
    findings = []
    print(f"Sync information profile — {len(files)} sync(s)")
    for fname in files:
        counts, conjuncts, d_sources, has_table = parse_sync(
            os.path.join(args.sync_dir, fname))
        stem = fname[:-len(".sync.md")]
        if not has_table:
            print(f"  {stem}: (no where-pattern table — unresolved skeleton?)")
            continue
        for k in total:
            total[k] += counts[k]
        bindings = sum(counts.values())
        print(f"  {stem}: A={counts['A']} B={counts['B']} C={counts['C']} "
              f"D={counts['D']} join={conjuncts}  ({bindings} binding"
              f"{'s' if bindings != 1 else ''})")
        for src in d_sources:
            findings.append(
                f"{stem}: D-read ({src.strip('| ').split(' | ')[-1]}) — "
                f"outcome instead of read? If this read decides something, "
                f"the owning concept could emit an outcome the sync routes on "
                f"(Pattern A) instead (concepts decide, syncs route).")
        if conjuncts >= _WIDE_JOIN:
            findings.append(
                f"{stem}: join arity {conjuncts} — {conjuncts} conjuncts is "
                f"real coordination knowledge in one rule; check the chain "
                f"table intends it.")

    bindings_all = sum(total.values())
    print(f"Aggregate: A={total['A']} B={total['B']} C={total['C']} "
          f"D={total['D']}  ({bindings_all} bindings)")
    print("  Reading: A adds zero; B adds chain-topology knowledge; C adds a "
          "copy point; D crosses a concept boundary.")
    if findings:
        print(f"\nWARN  {len(findings)} advisory finding(s):")
        for f in findings:
            print(f"  * {f}")
    else:
        print("\nPASS  no advisory findings — profile above is the review surface")
    # Advisory by construction: findings never change the exit code.
    return 0


if __name__ == "__main__":
    sys.exit(main())
