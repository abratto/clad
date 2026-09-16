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

GATE2_STATUS = re.compile(r"^- \*\*Gate 2 \([^)]*\):\*\*\s+`(\w+)`", re.MULTILINE)
GATE2_HASH = re.compile(r"^- \*\*Gate 2 content hash:\*\*\s+`([0-9a-f]+)`", re.MULTILINE)


def repo_root(feature_root: str) -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(feature_root)))


def corpus_dir(feature_root: str) -> str:
    value = cs.get_property(feature_root, "concepts.dir") or "features/_system/concepts"
    return os.path.join(repo_root(feature_root), value)


def feature_slug(feature_root: str) -> str:
    return os.path.basename(os.path.abspath(feature_root))


def stamp_provenance(text: str, slug: str) -> str:
    """Ensure the proposal carries `introduced-by <slug>`."""
    if re.search(r"^introduced-by\s+", text, re.MULTILINE):
        return text
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.strip().startswith("concept "):
            lines.insert(i + 1, f"introduced-by {slug}")
            return "\n".join(lines)
    return f"introduced-by {slug}\n{text}"


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
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4 or cells[0].startswith("---") or cells[0].startswith("<"):
            continue
        concept, _, _, requires = cells[0], cells[1], cells[2], cells[3]
        if requires and requires not in ("—", "-", "n/a"):
            claims.append((concept.strip("`"), requires.strip("`")))
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

    # Idempotency: same gate hash already promoted AND corpus copies match.
    if os.path.isfile(receipt) and not args.dry_run:
        with open(receipt, encoding="utf-8") as fh:
            if f"gate hash: `{gate_hash}`" in fh.read():
                same = all(
                    os.path.isfile(os.path.join(corpus, f"{c}.concept.md"))
                    and open(os.path.join(corpus, f"{c}.concept.md"),
                             encoding="utf-8").read() ==
                    stamp_provenance(open(p, encoding="utf-8").read(), slug)
                    for c, p in proposals.items())
                if same:
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
    for concept, path in sorted(proposals.items()):
        with open(path, encoding="utf-8") as fh:
            text = stamp_provenance(fh.read(), slug)
        with open(os.path.join(corpus, f"{concept}.concept.md"), "w",
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
    if claims:
        print("      Dependence claims to merge into concept-dependence.md "
              "(reviewed artefact):")
        for concept, requires in claims:
            print(f"        {concept} requires {requires}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
