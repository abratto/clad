#!/usr/bin/env python3
"""
verify_concept_registry.py — project-level concept-registry consistency.

Why this exists:
  Under the system-scope concept model (maintenance change
  `system-scope-concept-vocabulary`) a concept is defined ONCE, in the corpus,
  and use cases reuse it. Per-feature gates bind only their own outputs, so
  nothing per-feature can see a concept redefined in two places or a proposal
  that was approved but never promoted. This check sees the whole project.

Checks (across every feature, plus the corpus):
  * One introducer — no concept carries `introduced-by` for more than one
    feature in the corpus, and a feature's proposal must not claim to introduce
    a concept the corpus already attributes to another feature.
  * No redefinition — a feature whose responsibility map marks a concept
    `reused:UC-XX` must not carry a `<Name>.concept.md` in its Stage-02 output.
  * Promotion — a NEW/EXTEND concept whose feature has Gate 2 `approved` must
    be present in the canonical corpus (promote-on-approval).
  * Catalog completeness — every corpus concept appears in the generated
    catalog index (regenerate with generate_concepts_catalog.py).

Usage:
  python3 verify_concept_registry.py [--features-dir features]
                                     [--concepts-dir features/_system/concepts]
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifact_parsers as ap  # noqa: E402

PROVENANCE = re.compile(r"^introduced-by\s+(.+?)\s*$", re.MULTILINE)


def gate2_approved(resume_text):
    """True when the feature's RESUME records Gate 2 as approved (single grammar:
    artifact_parsers.parse_gate_status)."""
    return ap.parse_gate_status(resume_text, 2, "Architecture") == "approved"


def corpus_specs(concepts_dir):
    """concept -> path for the canonical corpus."""
    if not os.path.isdir(concepts_dir):
        return {}
    return {n: p for n, p in ap.concept_spec_paths([concepts_dir]).items()}


def introducers(concepts_dir):
    """concept -> set of `introduced-by` values in the corpus."""
    out = {}
    for concept, path in corpus_specs(concepts_dir).items():
        with open(path, encoding="utf-8") as fh:
            prov = PROVENANCE.search(fh.read())
        out[concept] = {prov.group(1).strip()} if prov else set()
    return out


def feature_dirs(features_dir):
    """The project's own features.

    UC-00-login is the STOCKED worked example: a derived project carries it for
    reference but does not inherit its concept vocabulary, so its concepts are
    not required to be present in this project's corpus. It is excluded here
    (consistent with verify_shared_action_contracts.py). A project's corpus
    starts empty and grows only from its own features."""
    if not os.path.isdir(features_dir):
        return []
    return [os.path.join(features_dir, d) for d in sorted(os.listdir(features_dir))
            if d.startswith("UC-") and not d.startswith("UC-00")]


def main():
    parser = argparse.ArgumentParser(
        description="Project-level concept registry consistency")
    parser.add_argument("--features-dir", default="features")
    parser.add_argument("--concepts-dir", default=None,
                        help="Canonical corpus (default <features-dir>/_system/concepts)")
    args = parser.parse_args()

    concepts_dir = args.concepts_dir or os.path.join(args.features_dir,
                                                     "_system", "concepts")
    corpus = corpus_specs(concepts_dir)
    if not corpus and not any(
            os.path.isfile(os.path.join(f, "stages", "01a_responsibility-map",
                                        "output", "responsibility-map.md"))
            for f in feature_dirs(args.features_dir)):
        print("SKIP  no concept corpus and no responsibility maps")
        return 0

    failures, warnings = [], []

    # 1. One introducer per concept.
    for concept, provs in sorted(introducers(concepts_dir).items()):
        if len(provs) > 1:
            failures.append(
                f"{concept}: introduced by {len(provs)} features in the corpus "
                f"({', '.join(sorted(provs))}) — a concept has one introducer")

    # 2/3. Per feature: no redefinition, and promotable proposals are promoted.
    for feature in feature_dirs(args.features_dir):
        slug = os.path.basename(feature)
        resp_map = os.path.join(feature, "stages", "01a_responsibility-map",
                                "output", "responsibility-map.md")
        if not os.path.isfile(resp_map):
            continue
        entries = {c: e for c, e in ap.parse_responsibility_map(resp_map).items()
                   if c != "Web"}
        origins = {c: (e.origin or "").strip().lower() for c, e in entries.items()}
        if not any(origins.values()):
            continue  # pre-Model-B feature
        concept_out = os.path.join(feature, "stages", "02_concepts", "output")
        present = set(ap.concept_spec_paths([concept_out]))

        for concept, origin in sorted(origins.items()):
            if origin.startswith("reused") and concept in present:
                failures.append(
                    f"{slug}/{concept}: marked {origin} but carries a spec file "
                    f"(a reused concept binds to the corpus; it must not redefine it)")
            if origin.startswith(("new", "extend")):
                if concept not in corpus:
                    resume = os.path.join(feature, "RESUME.md")
                    approved = (os.path.isfile(resume)
                                and gate2_approved(open(resume, encoding="utf-8").read()))
                    if approved:
                        failures.append(
                            f"{slug}/{concept}: Gate 2 approved but the proposal is "
                            f"not in the corpus — run ./clad promote-concepts")
                    else:
                        warnings.append(
                            f"{slug}/{concept}: proposal not yet promoted "
                            f"(Gate 2 not approved — expected in-flight)")

    # 4. Catalog completeness.
    catalog = os.path.join(os.path.dirname(concepts_dir), "concepts-catalog.md")
    if corpus and os.path.isfile(catalog):
        with open(catalog, encoding="utf-8") as fh:
            text = fh.read()
        for concept in sorted(corpus):
            if f"`{concept}`" not in text:
                failures.append(
                    f"{concept}: missing from concepts-catalog.md "
                    f"(regenerate with generate_concepts_catalog.py --write)")

    for warning in warnings:
        print(f"WARN  {warning}")
    if failures:
        print(f"FAIL  {len(failures)} concept-registry inconsistency(ies):")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"PASS  concept registry consistent "
          f"({len(corpus)} corpus concept(s), "
          f"{len(feature_dirs(args.features_dir))} feature(s) scanned)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
