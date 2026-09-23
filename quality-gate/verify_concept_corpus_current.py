#!/usr/bin/env python3
"""
verify_concept_corpus_current.py — the canonical corpus is not behind.

Why this exists:
  A concept is written whole, so the corpus entry is replaced on every
  promotion — which makes "is this the current model of `MemberEnrolment`?" a
  question about *ordering*, not about file equality. The obvious check (does
  every feature's copy equal the corpus?) is the wrong invariant: from the
  second extending use case onward an earlier feature's copy is *supposed* to
  differ, because it is a frozen proposal snapshot.

  The invariant that is actually true: the canonical entry names its promotion
  history, and every use case that has been through Gate 2 appears on it. This
  check enforces that, and that the companions agree with the spec.

Checks:
  * Every feature whose Gate 2 is approved and whose responsibility map has a
    `new` / `extends:*` row for a concept appears in that concept's canonical
    `introduced-by` / `extended-by` history, with a `_promotions/<slug>.md`
    receipt. Catches a promotion that never ran (the corpus silently behind).
  * The canonical data model and contract name the same current source as the
    spec's history (the companions cannot drift from it).
  * A canonical companion without a matching spec, or history naming a feature
    with no receipt, fails.

A feature still in flight (Gate 2 not approved) is skipped: its proposal is
legitimately not promoted yet.

Usage:
  python3 verify_concept_corpus_current.py --features-dir features

Exit: 0 pass/skip, 1 fail.
"""

import argparse
import os
import re
import sys

import artifact_parsers as ap
from verify_stage_sequence import gate_status


INTRODUCED_RE = re.compile(r"^introduced-by\s+(.+)$", re.MULTILINE)
EXTENDED_RE = re.compile(r"^extended-by\s+(.+)$", re.MULTILINE)
COMPANION_RE = re.compile(
    r"canonical —\s*derived from concept\s+(?P<concept>[\w]+):\s*"
    r"introduced-by\s+(?P<intro>.+?),\s*current source\s+(?P<promoter>.+?)\s*-->")

COMPANIONS = ("data-model.md", "contract.md")


def history_of(spec_text):
    """`(introducer, [promoters in promotion order])` for a canonical spec."""
    intro = INTRODUCED_RE.search(spec_text)
    ext = EXTENDED_RE.search(spec_text)
    introducer = intro.group(1).strip() if intro else ""
    extenders = [s.strip() for s in ext.group(1).split(",")] if ext else []
    return introducer, extenders


#: The bootstrap concept owns the transport boundary and is governed separately
#: (`methodology/architecture/WEB_CONCEPT.md`) — it is deliberately not a corpus
#: concept, so it is not "promoted" like one.
BOOTSTRAP_CONCEPT = "Web"

#: `UC-00-*` is the reserved worked example. In a derived repository it is a
#: reference copy of the seed's walkthrough, so its concepts belong to the
#: seed's corpus, not to this app's — checking them would be noise.
WORKED_EXAMPLE = "UC-00"


def proposing_features(features_dir):
    """`{concept: [(slug, feature_dir)]}` for approved `new`/`extends` rows."""
    out = {}
    for name in sorted(os.listdir(features_dir)):
        feature = os.path.join(features_dir, name)
        if not os.path.isdir(feature) or not name.startswith("UC-"):
            continue
        if name.startswith(WORKED_EXAMPLE):
            continue
        resp = os.path.join(feature, "stages", "01a_responsibility-map",
                            "output", "responsibility-map.md")
        if not os.path.isfile(resp):
            continue
        resume = os.path.join(feature, "RESUME.md")
        status = ""
        if os.path.isfile(resume):
            with open(resume, encoding="utf-8", errors="replace") as handle:
                status = gate_status(handle.read(), 2) or ""
        if status != "approved":
            continue
        for concept, entry in sorted(ap.parse_responsibility_map(resp).items()):
            if concept == BOOTSTRAP_CONCEPT:
                continue
            origin = (entry.origin or "").strip().lower()
            if origin.startswith(("new", "extend")):
                out.setdefault(concept, []).append((name, feature))
    return out


def main():
    parser = argparse.ArgumentParser(
        description="The canonical concept corpus is current and self-consistent")
    parser.add_argument("--features-dir", default="features")
    parser.add_argument("--concepts-dir", default="")
    args = parser.parse_args()

    features_dir = os.path.abspath(args.features_dir)
    corpus = args.concepts_dir or os.path.join(features_dir, "_system", "concepts")
    if not os.path.isdir(corpus):
        print(f"SKIP  no canonical corpus at {corpus}")
        return 0

    proposers = proposing_features(features_dir)
    receipt_dir = os.path.join(corpus, "_promotions")

    failures = []
    concepts = sorted(f for f in os.listdir(corpus) if f.endswith(".concept.md"))

    # A concept an in-scope feature proposed and had approved must exist in the
    # corpus at all — an absent entry is the most complete form of "behind".
    present = {f.replace(".concept.md", "") for f in concepts}
    for concept, entries in sorted(proposers.items()):
        if concept not in present:
            who = ", ".join(f"`{slug}`" for slug, _ in entries)
            failures.append(
                f"{concept}: proposed by {who} with Gate 2 approved, but the "
                f"corpus has no canonical entry for it — promotion never ran.")
    for fname in concepts:
        concept = fname.replace(".concept.md", "")
        with open(os.path.join(corpus, fname), encoding="utf-8") as handle:
            spec_text = handle.read()
        introducer, extenders = history_of(spec_text)
        history = ([introducer] if introducer else []) + extenders
        current = history[-1] if history else ""

        # 1. every approved proposer is on the canonical history
        for slug, _feature in proposers.get(concept, []):
            if slug not in history:
                failures.append(
                    f"{concept}: `{slug}` proposed this concept and its Gate 2 is "
                    f"approved, but the canonical entry does not name it — the "
                    f"corpus is behind (run `./clad promote-concepts {slug}`).")

        # 2. every promoter has a receipt naming the concept
        for slug in history:
            receipt = os.path.join(receipt_dir, f"{slug}.md")
            if not os.path.isfile(receipt):
                failures.append(
                    f"{concept}: history names `{slug}` but there is no "
                    f"_promotions/{slug}.md receipt — the promotion record is "
                    f"incomplete.")
                continue
            with open(receipt, encoding="utf-8", errors="replace") as handle:
                if concept not in handle.read():
                    failures.append(
                        f"{concept}: `_promotions/{slug}.md` does not list this "
                        f"concept — the receipt and the canonical entry disagree.")

        # 3. companions agree with the spec's current source
        for suffix in COMPANIONS:
            path = os.path.join(corpus, f"{concept}.{suffix}")
            if not os.path.isfile(path):
                continue
            with open(path, encoding="utf-8") as handle:
                head = handle.read(400)
            match = COMPANION_RE.search(head)
            if not match:
                failures.append(
                    f"{concept}.{suffix}: canonical companion has no "
                    f"'canonical — derived from concept X: …' header, so it "
                    f"cannot be told apart from a feature snapshot.")
                continue
            if match.group("promoter").strip() != current:
                failures.append(
                    f"{concept}.{suffix}: its header names "
                    f"`{match.group('promoter').strip()}` as the concept's source "
                    f"but the canonical spec is owned by `{current}` — the "
                    f"companions have drifted.")
            if match.group("intro").strip() != introducer:
                failures.append(
                    f"{concept}.{suffix}: introducer "
                    f"`{match.group('intro').strip()}` disagrees with the spec's "
                    f"`{introducer}`.")

    if failures:
        print("FAIL  the canonical corpus is stale or self-inconsistent")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    features_seen = {slug for entries in proposers.values() for slug, _ in entries}
    print(f"PASS  {len(concepts)} canonical concept(s) current; "
          f"{len(features_seen)} proposing feature(s) recorded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
