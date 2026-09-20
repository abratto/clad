#!/usr/bin/env python3
"""
promote_concepts.py — promote an approved feature's NEW/EXTEND concept
proposals into the canonical system-scope corpus.

Why this exists:
  Concepts are system-scope assets (maintenance change
  `system-scope-concept-vocabulary`, decisions D2/D5/S2). A feature authors its
  proposals in its own `02_concepts/output/`; they enter the canonical corpus
  ONLY on explicit promotion, and ONLY after the proposing feature's Gate 2 is
  approved. Promotion is never automatic and never silent.

What it does:
  1. Refuses unless the feature's Gate 2 (Architecture) is `approved` in
     RESUME.md (reuses the same gate-hash machinery as approve_gate.py).
  2. Copies each NEW/EXTEND proposal from the feature's Stage-02 output into
     `features/_system/concepts/<Name>.concept.md`, stamping provenance
     (`introduced-by <feature>`) when absent.
  3. Regenerates `features/_system/concepts-catalog.md`.
  4. Writes a promotion receipt under
     `features/_system/concepts/_promotions/<feature>.md` recording the
     gate content hash and the promoted concepts.
  5. Reports the proposals' extrinsic dependence claims. The app-level graph
     (`concept-dependence.md`) is REVIEWED, not derived (D4/S1), so it is never
     edited here — the human merges the claims and re-runs.

Idempotent: re-promoting the same proposals at the same Gate 2 hash is a no-op.
Refuses to write into a frozen feature's tree; the corpus is the only target.

Usage:
  python3 promote_concepts.py --feature features/UC-XX-<slug> [--dry-run]

Exit: 0 promoted/no-op, 1 refused/failed.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifact_parsers as ap  # noqa: E402
import clad_stages as cs  # noqa: E402

INTRODUCED_RE = re.compile(r"^introduced-by\s+(.+)$", re.MULTILINE)
EXTENDED_RE = re.compile(r"^extended-by\s+(.+)$", re.MULTILINE)

GATE2_STATUS = re.compile(r"^- \*\*Gate 2 \([^)]*\):\*\*\s+`(\w+)`", re.MULTILINE)
GATE2_HASH = re.compile(r"^- \*\*Gate 2 content hash:\*\*\s+`([0-9a-f]+)`", re.MULTILINE)


def repo_root(feature_root: str) -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(feature_root)))


def corpus_dir(feature_root: str) -> str:
    value = cs.get_property(feature_root, "concepts.dir") or "features/_system/concepts"
    return os.path.join(repo_root(feature_root), value)


def feature_slug(feature_root: str) -> str:
    return os.path.basename(os.path.abspath(feature_root))


class OutOfOrderPromotion(RuntimeError):
    """A feature older than the concept's current canonical tried to promote."""


def provenance_scope(text: str):
    """`(introducer, promoter)` for a canonical concept spec.

    The first promoter is `introduced-by`; each later one is appended to
    `extended-by`. The last entry of that list is the feature the canonical
    entry currently came from — the concept's own promotion order.
    """
    intro = INTRODUCED_RE.search(text)
    extenders = EXTENDED_RE.search(text)
    introducer = intro.group(1).strip() if intro else ""
    history = [s.strip() for s in extenders.group(1).split(",")] if extenders else []
    promoter = history[-1] if history else introducer
    return introducer, promoter


def _with_history(text: str, history) -> str:
    """Write the promotion history into the text, replacing any stale copy."""
    line = "extended-by " + ", ".join(history)
    own = EXTENDED_RE.search(text)
    if own:
        return text[:own.start()] + line + text[own.end():]
    own_intro = INTRODUCED_RE.search(text)
    return text[:own_intro.end()] + "\n" + line + text[own_intro.end():]


def stamp_provenance(text: str, slug: str, canonical_text: str = "") -> str:
    """Record `slug` as the concept's promoter, append-only.

    The promotion history is a property of the CANONICAL entry, not of the
    proposal that arrives for it — a proposal is a frozen snapshot with no
    memory of who came after it. So the history is read from the canonical
    entry and written back into the text being promoted.

    A concept is written whole, so re-promoting an OLDER feature over a newer
    canonical entry would silently roll the corpus back — that is exactly how a
    superseded proposal once replaced the canonical `MemberEnrolment` spec and
    dropped the `verify` action. Only the concept's current source may write.
    """
    intro = INTRODUCED_RE.search(text) or INTRODUCED_RE.search(canonical_text)
    if intro is None:
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith("concept "):
                lines.insert(i + 1, f"introduced-by {slug}")
                return "\n".join(lines)
        return f"introduced-by {slug}\n{text}"

    introducer = intro.group(1).strip()
    if INTRODUCED_RE.search(text) is None:
        text = text[:intro.end()] + text[intro.end():]
    # History comes from the canonical when it has one, otherwise this text is
    # the first promotion and the introducer owns it.
    source = canonical_text if EXTENDED_RE.search(canonical_text) else text
    ext = EXTENDED_RE.search(source)
    history = [s.strip() for s in ext.group(1).split(",")] if ext else []
    current = history[-1] if history else introducer

    if slug == current:
        # Idempotent re-promotion by the concept's current source — but still
        # re-emit the history, which lives on the canonical, not on the frozen
        # proposal text.
        return _with_history(text, history) if history else text
    if slug == introducer or slug in history:
        raise OutOfOrderPromotion(
            f"`{slug}` has already promoted this concept, and `{current}` is its "
            f"current canonical source. Promoting `{slug}` now would roll the "
            f"corpus back to an older proposal.")

    history.append(slug)
    return _with_history(text, history)


LEADING_COMMENT_RE = re.compile(r"\A<!--.*?-->\n", re.DOTALL)


def canonical_companion(text: str, concept: str, introducer: str,
                        promoter: str) -> str:
    """The canonical form of a promoted model/contract.

    The generator's proposal-snapshot header is replaced by one that says what
    the file is and where its concept currently stands, so a reader of the
    corpus (or of a feature copy) can tell the two apart at a glance. The
    provenance recorded is the CONCEPT's — a companion is derived from the
    concept, and the concept is what moves between use cases.
    """
    header = (f"<!-- canonical — derived from concept {concept}: "
              f"introduced-by {introducer}, current source {promoter} -->\n")
    if LEADING_COMMENT_RE.match(text):
        return LEADING_COMMENT_RE.sub(header, text, count=1)
    return header + text


def proposals_for(feature_root: str):
    """(concept -> path) for the feature's NEW/EXTEND proposals."""
    resp_map = os.path.join(feature_root, "stages", "01a_responsibility-map",
                            "output", "responsibility-map.md")
    concept_out = os.path.join(feature_root, "stages", "02_concepts", "output")
    entries = ap.parse_responsibility_map(resp_map) if os.path.isfile(resp_map) else {}
    wanted = {
        c for c, e in entries.items()
        if (e.origin or "").strip().lower().startswith(("new", "extend"))
    }
    return {c: p for c, p in ap.concept_spec_paths([concept_out]).items()
            if c in wanted}


def dependence_claims(feature_root: str):
    """Concepts listed in the responsibility map's Proposals `Requires` column."""
    resp_map = os.path.join(feature_root, "stages", "01a_responsibility-map",
                            "output", "responsibility-map.md")
    if not os.path.isfile(resp_map):
        return []
    with open(resp_map, encoding="utf-8") as fh:
        text = fh.read()
    section = re.search(r"^##\s+Proposals\s*$(.*?)(?=^##\s|\Z)", text,
                        re.MULTILINE | re.DOTALL)
    if not section:
        return []
    claims = []
    for line in section.group(1).splitlines():
        if not line.startswith("|"):
            continue
        # Cells may contain ESCAPED pipes — the concept grammar writes
        # `[ ok \| refused ]` — so split on unescaped `|` only.
        cells, current, escaped = [], [], False
        for ch in line.strip().strip("|"):
            if escaped:
                current.append(ch)
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == "|":
                cells.append("".join(current).strip())
                current = []
            else:
                current.append(ch)
        cells.append("".join(current).strip())
        if len(cells) < 4 or cells[0].startswith("---") or cells[0].startswith("<"):
            continue
        # Skip the header row (`| Concept | Kind | ... |`).
        if cells[0].strip("`").strip().lower() == "concept":
            continue
        concept = cells[0].strip("`")
        # The claims column lists CONCEPTS, backticked and comma-separated; any
        # qualifier (`*(unchanged)*`) is prose for the reviewer. Extract the
        # backticked names rather than trusting the whole cell.
        for target in re.findall(r"`([^`]+)`", cells[3]):
            target = target.strip()
            if target and target not in ("—", "-", "n/a"):
                claims.append((concept, target))
    return claims


def main():
    parser = argparse.ArgumentParser(
        description="Promote approved NEW/EXTEND proposals into the concept corpus")
    parser.add_argument("--feature", required=True, help="Feature root")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would be promoted; write nothing")
    args = parser.parse_args()

    feature_root = os.path.abspath(args.feature)
    slug = feature_slug(feature_root)
    resume = os.path.join(feature_root, "RESUME.md")
    if not os.path.isfile(resume):
        print(f"FAIL  RESUME.md not found at {resume}")
        return 1

    with open(resume, encoding="utf-8") as fh:
        resume_text = fh.read()
    status = GATE2_STATUS.search(resume_text)
    if not status or status.group(1) != "approved":
        print("FAIL  Gate 2 (Architecture) is not approved — promotion refused.")
        print("      Approve Gate 2 first (./clad approve 2).")
        return 1
    gate_hash = GATE2_HASH.search(resume_text)
    gate_hash = gate_hash.group(1) if gate_hash else "unknown"

    proposals = proposals_for(feature_root)
    claims = dependence_claims(feature_root)

    if not proposals:
        print("SKIP  no NEW/EXTEND proposals to promote (this feature reuses the corpus)")
        return 0

    corpus = corpus_dir(feature_root)
    receipt_dir = os.path.join(corpus, "_promotions")
    receipt = os.path.join(receipt_dir, f"{slug}.md")

    def expected_canonical(concept, proposal_path):
        """The corpus text this promotion would write.

        `(spec, {suffix: text})` — the spec gains the promoter history, and each
        companion artefact (model, contract) carries the canonical header. A
        companion this feature did not re-derive is re-stamped anyway: the
        CONCEPT moved, so the canonical companion must name its new source, and
        its body is untouched.
        """
        canonical_path = os.path.join(corpus, f"{concept}.concept.md")
        existing = ""
        if os.path.isfile(canonical_path):
            with open(canonical_path, encoding="utf-8") as fh:
                existing = fh.read()
        with open(proposal_path, encoding="utf-8") as fh:
            spec = stamp_provenance(fh.read(), slug, existing)
        introducer, promoter = provenance_scope(spec)
        companions = {}
        for rel, suffix in (("03b_data-model", "data-model.md"),
                            ("04_implement/04b_contract", "contract.md")):
            produced = os.path.join(feature_root, "stages", rel, "output",
                                    f"{concept}.{suffix}")
            canonical = os.path.join(corpus, f"{concept}.{suffix}")
            source = produced if os.path.isfile(produced) else canonical
            if not os.path.isfile(source):
                continue
            with open(source, encoding="utf-8") as fh:
                companions[suffix] = canonical_companion(
                    fh.read(), concept, introducer, promoter)
        return spec, companions

    # Refusal is per concept: a feature that extends several concepts may be the
    # current source of some and an older source of others. Read-only refusals
    # are skipped (never silently rolled back), and reported at the end.
    planned, refused = {}, []
    for concept, path in sorted(proposals.items()):
        try:
            planned[concept] = expected_canonical(concept, path)
        except OutOfOrderPromotion as refusal:
            refused.append((concept, str(refusal)))

    # Idempotency: same gate hash already promoted AND the corpus matches.
    if os.path.isfile(receipt) and not args.dry_run:
        with open(receipt, encoding="utf-8") as fh:
            if f"gate hash: `{gate_hash}`" in fh.read():
                def _same(concept) -> bool:
                    spec, companions = planned[concept]
                    path = os.path.join(corpus, f"{concept}.concept.md")
                    if not (os.path.isfile(path)
                            and open(path, encoding="utf-8").read() == spec):
                        return False
                    for suffix, text in companions.items():
                        companion = os.path.join(corpus, f"{concept}.{suffix}")
                        if not (os.path.isfile(companion)
                                and open(companion, encoding="utf-8").read() == text):
                            return False
                    return True

                # `planned` is empty when every concept was refused as
                # out-of-order — that is not a no-op, it is a refusal.
                if planned and all(_same(c) for c in planned):
                    print(f"PASS  already promoted at Gate 2 hash `{gate_hash[:12]}…` — no-op")
                    return 0

    if args.dry_run:
        print(f"WOULD promote {len(proposals)} concept(s) into {cs.relpath(corpus, repo_root(feature_root))}:")
        for concept in sorted(proposals):
            print(f"  - {concept}.concept.md  (introduced-by {slug})")
        for concept, requires in claims:
            print(f"  dependence claim: {concept} requires {requires}")
        print("(dry run — nothing written)")
        return 0

    os.makedirs(corpus, exist_ok=True)
    os.makedirs(receipt_dir, exist_ok=True)
    promoted = []
    for concept in sorted(planned):
        spec, companions = planned[concept]
        with open(os.path.join(corpus, f"{concept}.concept.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(spec)
        # The conceptual data model and the concept contract are canonical too:
        # they live beside the spec, promoted with it. A reused concept binds
        # the canonical artefact rather than deriving a second copy.
        for suffix, text in companions.items():
            with open(os.path.join(corpus, f"{concept}.{suffix}"), "w",
                      encoding="utf-8") as fh:
                fh.write(text)
        promoted.append(concept)

    # Regenerate the catalog index.
    subprocess.run([sys.executable,
                    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "generate_concepts_catalog.py"),
                    "--concepts-dir", corpus,
                    "--features-dir", os.path.join(repo_root(feature_root), "features"),
                    "--write"], check=True)

    with open(receipt, "w", encoding="utf-8") as fh:
        fh.write(f"# Promotion receipt — `{slug}`\n\n")
        fh.write(f"- gate hash: `{gate_hash}`\n")
        fh.write(f"- promoted concepts: {', '.join(f'`{c}`' for c in promoted)}\n")
        if claims:
            fh.write("- dependence claims (merge into `concept-dependence.md`, "
                     "which is reviewed, not generated):\n")
            for concept, requires in claims:
                fh.write(f"  - `{concept}` requires `{requires}`\n")

    print(f"PASS  promoted {len(promoted)} concept(s) into the corpus: "
          f"{', '.join(promoted)}")
    for concept, reason in refused:
        print(f"WARN  skipped `{concept}` — {reason}")
        print("      The corpus must not move backwards. Promote the feature "
              "that currently owns the concept, or record an R20 maintenance "
              "change before re-promoting this one.")
    if claims:
        print("      Dependence claims to merge into concept-dependence.md "
              "(reviewed artefact):")
        for concept, requires in claims:
            print(f"        {concept} requires {requires}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
