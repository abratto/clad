#!/usr/bin/env python3
"""
generate_syncs.py — deterministic Stage 03 sync generation.

Each non-root, non-terminal chain-table row becomes one *.sync.md file, with
the Sync Contract Matrix, the `when`/`where`/`then` rule block, the A/B/C/D
pattern table, and the compressed-rule name — all derived mechanically from
the canonical chain tables in 01b and the concept specs in 02.

What this generator does NOT decide (and never guesses):

  * Pattern D concept-state reads. When the target action needs a field that
    is neither a carried field on the trigger outcome nor a literal, the
    generator emits a `<!-- TODO PATTERN-D ... -->` marker instead of inventing
    a cross-concept state read. The agent resolves these by LLM after the
    deterministic skeleton is written.

Usage:
  python3 generate_syncs.py --feature <features/UC-XX-slug>
  python3 generate_syncs.py --feature <features/UC-XX-slug> --write   # write files

Without --write it prints what it would emit (dry run).
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import artifact_parsers as ap
import clad_stages as cs


# --------------------------------------------------------------------------
# Per-row sync derivation
# --------------------------------------------------------------------------

@dataclass
class GeneratedSync:
    name: str
    stem: str
    trigger_concept: str
    trigger_action: str
    trigger_completion: str
    target_concept: str
    target_action: str
    source_row: str
    target_row: str
    when_sig: str
    then_sig: str
    literals: str
    binds: List[Tuple[str, str, str]]  # (var, pattern, source)
    pattern_d_notes: List[str]
    cited_scenario: str


def completion_token(outcome_base: str) -> str:
    """Map an outcome token to its PascalCase sync-name completion."""
    if not outcome_base:
        return ""
    if outcome_base.lower() in ("refused",):
        return "Refused"
    return ap.first_completion_token(outcome_base)


def derive_syncs_for_feature(feature_root: str) -> Tuple[List[GeneratedSync], List[str]]:
    chain_dir = cs.CHAIN_DIR(feature_root)
    concept_dir = cs.CONCEPT_DIR(feature_root)
    scope = ap.feature_scope_from_path(feature_root)

    concepts: Dict[str, ap.ConceptSpec] = {}
    if os.path.isdir(concept_dir):
        for fname in sorted(os.listdir(concept_dir)):
            if fname.endswith(".concept.md"):
                c = ap.parse_concept(os.path.join(concept_dir, fname))
                concepts[c.name] = c

    syncs: List[GeneratedSync] = []
    warnings: List[str] = []

    for fname in sorted(os.listdir(chain_dir)):
        if not fname.endswith("-chain.md") or fname.endswith("-all-scenarios-chain.md"):
            continue
        rows = ap.parse_chain_table(os.path.join(chain_dir, fname))
        scenario = fname.replace("-chain.md", "")

        # Row 0 is the Web entry (Web/request -> Web.request) — not a sync.
        # Every other row i (including terminal Web.respond rows) is one sync:
        #   when = row(i-1) action + outcome, then = row(i) action.
        for idx in range(1, len(rows)):
            row = rows[idx]
            prev = rows[idx - 1]

            trigger_concept = prev.then_concept
            trigger_action = prev.then_action
            trigger_outcome_raw = prev.outcome_base
            trigger_completion = completion_token(trigger_outcome_raw)

            target_concept = row.then_concept
            target_action = row.then_action

            base = (
                "When"
                + ap.pascal_token(trigger_concept)
                + ap.pascal_token(trigger_action)
                + ap.first_completion_token(trigger_outcome_raw)
                + "Then"
                + ap.pascal_token(target_concept)
                + ap.pascal_token(target_action)
            )
            stem = base + (f"For{scope}" if scope else "")

            source_row_id = str(prev.row_num)
            target_row_id = str(row.row_num)

            when_sig = (f"{trigger_concept}/{trigger_action}: [...] => "
                        f"[ {trigger_outcome_raw} ]")
            then_sig = f"{target_concept}/{target_action}: [ <args> ]"
            literals = "<none>"

            binds: List[Tuple[str, str, str]] = []
            pattern_d_notes: List[str] = []
            if prev.outcome_payload:
                var = "?" + prev.outcome_payload
                binds.append((var, "A", f"Trigger token (`{trigger_concept}/{trigger_action}`)"))

            syncs.append(GeneratedSync(
                name=stem,
                stem=stem,
                trigger_concept=trigger_concept,
                trigger_action=trigger_action,
                trigger_completion=trigger_completion,
                target_concept=target_concept,
                target_action=target_action,
                source_row=source_row_id,
                target_row=target_row_id,
                when_sig=when_sig,
                then_sig=then_sig,
                literals=literals,
                binds=binds,
                pattern_d_notes=pattern_d_notes,
                cited_scenario=scenario,
            ))

    # A sync is defined once, not once per scenario that traverses it. Dedup by
    # stem, keeping first occurrence (canonical scenario order).
    seen: Set[str] = set()
    unique: List[GeneratedSync] = []
    for g in syncs:
        if g.stem not in seen:
            seen.add(g.stem)
            unique.append(g)
    return unique, warnings


def render_sync(g: GeneratedSync) -> str:
    lines: List[str] = []
    lines.append(f"sync {g.name}")
    lines.append("")
    lines.append("## Sync Contract Matrix")
    lines.append("")
    lines.append("| Source row | Target row | `when` signature | `then` signature | Allowed literals |")
    lines.append("|---|---|---|---|---|")
    lines.append(f"| `{g.source_row}` | `{g.target_row}` | `{g.when_sig}` | `{g.then_sig}` | `{g.literals}` |")
    lines.append("")
    lines.append("## Rule")
    lines.append("")
    lines.append("```")
    lines.append("when {")
    lines.append(f"    {g.trigger_concept}/{g.trigger_action}: [ ... ] => [ {g.trigger_completion} ; ... ]")
    lines.append("}")
    if g.binds or g.pattern_d_notes:
        lines.append("where {")
        for var, _patt, _src in g.binds:
            lines.append(f"    bind ( <source> as {var} )")
        lines.append("}")
    lines.append("then {")
    lines.append(f"    {g.target_concept}/{g.target_action}: [ <args> ]")
    lines.append("}")
    lines.append("```")
    lines.append("")
    lines.append("## Where clause patterns (for Stage 03a audit)")
    lines.append("")
    lines.append("| Binding | Pattern | Source |")
    lines.append("|---|---|---|")
    if g.binds:
        for var, patt, src in g.binds:
            lines.append(f"| `{var}` | {patt} | {src} |")
    # TODO markers for the agent.
    lines.append("")
    lines.append("<!-- TODO (agent) — fill `<source>` and `<args>` above; add any Pattern D")
    lines.append("     concept-state read here if this sync must reach into another concept's")
    lines.append("     state. Do not invent a read that the chain table did not authorize. -->")
    lines.append("")
    lines.append("## Cites")
    lines.append("")
    lines.append(f"- `../01_usecase/output/usecase.md` — scenario \"{g.cited_scenario}\"")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministically generate Stage 03 syncs")
    parser.add_argument("--feature", required=True, help="Feature root path")
    parser.add_argument("--write", action="store_true", help="Write files (default dry-run)")
    args = parser.parse_args()

    feature_root = os.path.abspath(args.feature)
    sync_dir = cs.SYNC_DIR(feature_root)

    syncs, warnings = derive_syncs_for_feature(feature_root)
    for w in warnings:
        print(f"WARN  {w}")

    if not syncs:
        print("No syncs derivable (no canonical chain tables found).")
        sys.exit(0)

    for g in syncs:
        out_path = os.path.join(sync_dir, g.stem + ".sync.md")
        if args.write:
            os.makedirs(sync_dir, exist_ok=True)
            with open(out_path, "w") as fh:
                fh.write(render_sync(g) + "\n")
            print(f"WROTE {cs.relpath(out_path, feature_root)}")
        else:
            print(f"WOULD WRITE {g.stem}.sync.md  [{g.trigger_concept}/{g.trigger_action}[{g.trigger_completion}] -> {g.target_concept}/{g.target_action}]")

    if not args.write:
        print(f"\n{len(syncs)} syncs (dry run). Re-run with --write to emit files.")


if __name__ == "__main__":
    main()
