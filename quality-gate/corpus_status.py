#!/usr/bin/env python3
"""
corpus_status.py — read-only health report for the canonical concept corpus
(maintenance change `corpus-status-command`).

Why this exists:
  The corpus accumulates history one promotion at a time, and nothing
  surfaced its shape: which concepts are load-bearing (high dependence
  in-degree), which have been extended repeatedly (first-proposer bias
  hurts most there — those are the `remodel` candidates), and which
  features hold proposal snapshots that no longer match the canonical
  entry. This report makes that visible without opening every file.

Per concept it reports:
  * current source     — the last feature in the promotion history
  * history            — `introduced-by` + `extended-by`, in order
  * history depth      — number of promoting features; depth above
                         `--remodel-depth` (default 3) flags the concept as
                         a remodel candidate
  * stale snapshots    — features whose Stage-02 copy differs from the
                         canonical entry (expected once a later feature has
                         extended it; a snapshot is a Gate-2 audit trail,
                         never current truth)
  * in-degree          — edges INTO the concept in the reviewed app-level
                         dependence graph (`concept-dependence.md`)

Sorted by in-degree descending, then name. READ-ONLY: writes nothing.
Exit 0 always.

Usage:
  python3 corpus_status.py [--features-dir features] [--remodel-depth 3]
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import promote_concepts as pc  # noqa: E402


def concept_history(text):
    """(introducer, [extenders]) from a canonical spec's provenance lines."""
    intro = pc.INTRODUCED_RE.search(text)
    ext = pc.EXTENDED_RE.search(text)
    introducer = intro.group(1).strip() if intro else ""
    extenders = [s.strip() for s in ext.group(1).split(",")] if ext else []
    return introducer, extenders


def stale_snapshots(features_dir, concept, canonical_text):
    """Features whose Stage-02 copy of the concept differs from canonical."""
    stale = []
    if not os.path.isdir(features_dir):
        return stale
    for name in sorted(os.listdir(features_dir)):
        path = os.path.join(features_dir, name, "stages", "02_concepts",
                            "output", concept + ".concept.md")
        if not name.startswith("UC-") or not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as handle:
            if handle.read() != canonical_text:
                stale.append(name)
    return stale


def in_degrees(features_dir):
    """Concept -> number of dependence edges INTO it, from the reviewed
    concept-dependence.md edges table."""
    degrees = {}
    graph = os.path.join(features_dir, "_system", "concept-dependence.md")
    if not os.path.isfile(graph):
        return degrees
    with open(graph, encoding="utf-8", errors="replace") as handle:
        in_table = False
        for line in handle:
            if line.lstrip().startswith("| Concept |"):
                in_table = True
                continue
            if in_table:
                if re.match(r"^\|[\s\-:]+\|", line):
                    continue
                if not line.startswith("|"):
                    in_table = False
                    continue
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) < 2:
                    continue
                for target in re.findall(r"`([^`]+)`", cells[1]):
                    degrees[target] = degrees.get(target, 0) + 1
    return degrees


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only health report for the canonical concept corpus")
    parser.add_argument("--features-dir", default="features")
    parser.add_argument("--remodel-depth", type=int, default=3,
                        help="History depth above which a concept is flagged "
                             "as a remodel candidate (default 3)")
    args = parser.parse_args()

    corpus = os.path.join(args.features_dir, "_system", "concepts")
    specs = sorted(f for f in os.listdir(corpus)
                   if f.endswith(".concept.md")) if os.path.isdir(corpus) else []
    if not specs:
        print(f"Corpus is empty ({corpus}) — promote a feature's concepts "
              f"at Gate 2 to populate it.")
        return 0

    degrees = in_degrees(args.features_dir)
    rows = []
    for fname in specs:
        concept = fname[:-len(".concept.md")]
        with open(os.path.join(corpus, fname), encoding="utf-8") as handle:
            text = handle.read()
        introducer, extenders = concept_history(text)
        history = [introducer] + extenders if introducer else extenders
        rows.append({
            "concept": concept,
            "current": history[-1] if history else "—",
            "history": history,
            "depth": len(history),
            "stale": stale_snapshots(args.features_dir, concept, text),
            "in_degree": degrees.get(concept, 0),
        })

    rows.sort(key=lambda r: (-r["in_degree"], r["concept"]))

    print(f"# Corpus status — {len(rows)} concept(s)\n")
    for row in rows:
        flags = []
        if row["depth"] > args.remodel_depth:
            flags.append(f"REMODEL CANDIDATE (history depth {row['depth']} "
                         f"> {args.remodel_depth})")
        if row["stale"]:
            flags.append(f"stale snapshot(s): {', '.join(row['stale'])}")
        print(f"  {row['concept']}")
        print(f"    current source : {row['current']}")
        print(f"    history        : "
              f"{', '.join(row['history']) if row['history'] else '—'}")
        print(f"    in-degree      : {row['in_degree']}")
        for flag in flags:
            print(f"    flag           : {flag}")
    candidates = [r["concept"] for r in rows
                  if r["depth"] > args.remodel_depth]
    if candidates:
        print(f"\nRemodel candidates: {', '.join(candidates)} — deeply "
              f"extended concepts are where first-proposer bias hurts most; "
              f"see RULES.md R22 (`remodel`).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
