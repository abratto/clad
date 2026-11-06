#!/usr/bin/env python3
"""
verify_rmap_companion_fresh.py — a feature that is a concept's current source
must have refreshed the canonical data-model companion before its migration is
generated.

Why this exists (experiment finding 29):
  `rmap.py --features-dir features` treats the canonical corpus as authoritative
  (`_project_sources`). So a feature that re-derives its Stage-03b model (say,
  adding a `title` fact) but has NOT refreshed the canonical
  `features/_system/concepts/<Name>.data-model.md` gets a migration generated
  from the STALE companion — silently omitting the new column. The only symptom
  is a wrong migration; nothing fails. The fix is to fail loudly here and tell
  the author to run `./clad promote-concepts <feature> --companions-only`.

Scope:
  Only a concept's CURRENT SOURCE is checked. An earlier feature's frozen 03b
  model legitimately differs from the canonical (it predates later additions —
  finding 32), so it is skipped. If the current source has no 03b model for the
  concept (a read-only feature), there is nothing to compare and it is skipped.

Usage:
  python3 verify_rmap_companion_fresh.py --feature features/UC-XX-<slug> [--corpus DIR]

Exit: 0 pass/skip, 1 fail.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifact_parsers as ap  # noqa: E402
import check_runner as cr  # noqa: E402
import rmap  # noqa: E402

INTRODUCED_RE = re.compile(r"^introduced-by\s+(.+)$", re.MULTILINE)
EXTENDED_RE = re.compile(r"^extended-by\s+(.+)$", re.MULTILINE)


def _current_source(concept_text):
    """The slug allowed to write the canonical entry: last `extended-by`, else
    `introduced-by`."""
    intro = INTRODUCED_RE.search(concept_text)
    ext = EXTENDED_RE.search(concept_text)
    introducer = intro.group(1).strip() if intro else ""
    history = [s.strip() for s in ext.group(1).split(",")] if ext else []
    return history[-1] if history else introducer


def _descriptor(concept, text):
    return rmap.model_descriptor([rmap.derive_model(concept, text)])


def findings(feature_root, corpus):
    slug = os.path.basename(os.path.abspath(feature_root))
    data_dir = os.path.join(feature_root, "stages", "03b-data-model", "output")
    if not os.path.isdir(data_dir):
        return []
    out = []
    for name in sorted(os.listdir(data_dir)):
        if not name.endswith(".data-model.md"):
            continue
        concept = name[:-len(".data-model.md")]
        spec_path = os.path.join(corpus, concept + ".concept.md")
        companion = os.path.join(corpus, concept + ".data-model.md")
        if not (os.path.isfile(spec_path) and os.path.isfile(companion)):
            continue  # not promoted / no companion yet — nothing to protect
        with open(spec_path, encoding="utf-8") as fh:
            if _current_source(fh.read()) != slug:
                continue  # frozen earlier feature — legitimately differs (#32)
        with open(os.path.join(data_dir, name), encoding="utf-8") as fh:
            feature_text = fh.read()
        with open(companion, encoding="utf-8") as fh:
            companion_text = fh.read()
        try:
            fresh = _descriptor(concept, feature_text)
            published = _descriptor(concept, companion_text)
        except ValueError:
            continue  # a malformed model is another check's job
        if fresh != published:
            out.append(
                f"{concept}: the canonical data-model companion "
                f"`{os.path.relpath(companion)}` is stale relative to this "
                f"feature's Stage-03b derivation — the migration would be "
                f"generated from the old model. Run "
                f"`./clad promote-concepts {slug} --companions-only`.")
    return out


def main(argv=None) -> int:
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--feature", required=True)
        parser.add_argument("--corpus", default="",
                            help="Canonical corpus dir (default: the feature's)")

    def body(args: argparse.Namespace) -> cr.Verdict:
        feature_root = os.path.abspath(args.feature)
        corpus = args.corpus or ap._default_corpus_dir(feature_root)
        if not os.path.isdir(corpus):
            return cr.Verdict.skip("no canonical corpus — nothing to protect")
        problems = findings(feature_root, corpus)
        if problems:
            return cr.Verdict.fail(
                "canonical data-model companion is stale — refresh before 04a",
                [cr.Problem(p, bullet=True) for p in problems])
        return cr.Verdict.ok(
            "canonical data-model companions match this feature's 03b derivation")

    return cr.run_check(
        "A current-source feature refreshed its canonical data-model companion",
        body, argv, configure)


if __name__ == "__main__":
    sys.exit(main())
