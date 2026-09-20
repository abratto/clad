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
import re
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
    is_join: bool = False
    conjuncts: List[Tuple[Optional[str], str, str, str]] = field(default_factory=list)
    # ^ (name, concept, action, outcome_raw) in declared conjunct order
    trigger_outcome_raw: str = ""
    # ^ the raw trigger outcome (single-trigger rules); needed to re-derive the
    #   stem at a higher escalation level when two short names collide.
    route: Optional[str] = None
    # The flow pin (maintenance/sync-flow-pinning.md): every non-bootstrap rule
    # names its flow root first, with the route matcher, so it can only fire in
    # its own flow. The pin is excluded from the stem — it is in every such rule,
    # so it discriminates nothing — while the route on a *bootstrap* is a
    # component, because only some rules have one.
    flow_route: Optional[str] = None
    flow_method: Optional[str] = None
    method: Optional[str] = None
    # ^ when-matcher scope literals for a `Web/request` bootstrap sync (R15);
    #   rendered into the generated `.sync.md` so the author need not add them.


def completion_token(outcome_base: str) -> str:
    """Map an outcome token to its PascalCase sync-name completion."""
    if not outcome_base:
        return ""
    if outcome_base.lower() in ("refused",):
        return "Refused"
    return ap.first_completion_token(outcome_base)


def completion_with_payload(outcome_raw: str) -> str:
    """PascalCase completion including any outcome payload.

    Two outcomes of one action may differ only in payload
    (`Released` vs `Released(blankFields)`); the sync stem must stay
    unique across them, so the payload joins the completion token
    (`...ReleasedBlankFields`). Matches the conduit rebuild
    experiment (maintenance/generate-syncs-branch-carriers.md).
    """
    name = ap.first_completion_token(outcome_raw)
    m = re.search(r"\(([^)]*)\)", outcome_raw or "")
    if not m:
        return name
    payload = "".join(
        w.capitalize() for w in re.split(r"[^A-Za-z0-9]+", m.group(1)) if w)
    # skip a payload that names nothing (bare type name == base token)
    if not payload or payload.lower() == name.lower():
        return name
    return name + payload


def _resolve_when_source(wc, wa, wo, producers, current_row, warnings, fname):
    """Resolve one `when` token to its producer row + trigger outcome raw.

    Branch-safe completion matching (not adjacent position): the producer is
    an earlier row P whose `Then` action equals this token's action and whose
    `Outcome` equals its completion. Returns `None` for a root row. Mirrors
    the long-standing single-trigger matching so single rows are unchanged.
    """
    wo_base = re.sub(r"\(.*?\)", "", wo).strip()
    action_matches = [prow for (pc, pa, po, prow) in producers
                      if pc == wc and pa == wa and prow is not current_row]
    # Prefer the exact-outcome producer, then any action match; the
    # outcome-mismatch case is the extension-row carrier (the chain table's
    # rows 7-9 shape) — conduit rebuild experiment, maintenance/
    # generate-syncs-branch-carriers.md.
    matches = [a for a in action_matches
               if ap.normalize_outcome(a.outcome_base)
               == ap.normalize_outcome(wo_base)]
    # Prefer the producer whose raw outcome equals the row's When token
    # verbatim: two rows of one action may differ only in outcome payload.
    raw_matches = [a for a in matches
                   if (getattr(a, "outcome_raw", "") or "").strip("\"") == wo]
    picked = raw_matches or matches
    if picked:
        prev = picked[0]
        trigger_outcome_raw = getattr(prev, "outcome_raw", None) or prev.outcome_base
    elif action_matches:
        prev = action_matches[0]
        trigger_outcome_raw = wo_base  # extension outcome (branch row)
    else:
        return None
    if len(action_matches) > 1 and len(action_matches) != len(matches):
        warnings.append(
            f"{fname} row {current_row.row_num}: {len(action_matches)} rows produce "
            f"{wc}/{wa}; using row {prev.row_num} "
            f"(outcome {trigger_outcome_raw})")
    return prev, trigger_outcome_raw


def derive_syncs_for_feature(feature_root: str) -> Tuple[List[GeneratedSync], List[str]]:
    chain_dir = cs.CHAIN_DIR(feature_root)
    # Concept sources: the feature's own proposals shadow the canonical corpus
    # by concept name (M1 union resolution).
    concepts: Dict[str, ap.ConceptSpec] = {}
    for name, path in ap.concept_spec_paths(cs.concept_source_dirs(feature_root)).items():
        concepts[name] = ap.parse_concept(path)

    syncs: List[GeneratedSync] = []
    warnings: List[str] = []

    for fname in sorted(os.listdir(chain_dir)):
        if not fname.endswith("-chain.md") or fname.endswith("-all-scenarios-chain.md"):
            continue
        rows = ap.parse_chain_table(os.path.join(chain_dir, fname))
        scenario = fname.replace("-chain.md", "")

        # The flow root (row 1) carries the route/method in its When cell, e.g.
        # `Web/request[route: "tags" ; method: "GET"]`. The bootstrap sync
        # (`Web.request -> <first action>`) must keep that as its R15 route
        # matcher. Authors previously added it by hand every UC.
        root_route = root_method = None
        if rows:
            root_when = rows[0].when or ""
            m = re.search(r'route\s*:\s*"([^"]+)"', root_when)
            if m:
                root_route = m.group(1)
            else:
                # A chain table writes the flow root as `Web/request[POST /loans]`
                # (method + path), so the route is the resource segment. Without
                # this the bootstrap got no route matcher at all and two routes
                # bootstrapping one action produced identical names.
                m = re.search(r'\b([A-Z]+)\s+/([A-Za-z0-9_-]+)', root_when)
                if m:
                    root_method, root_route = m.group(1), m.group(2)
            m = re.search(r'method\s*:\s*"([^"]+)"', root_when)
            if m:
                root_method = m.group(1)

        # Derive the invocation graph by matching completions, not by adjacent
        # position: a row R is driven by an earlier row P whose `Then` action is
        # R's `When` action and whose `Outcome` is R's `When` completion. This
        # is branch-safe — a row that opens an extension branch points back to
        # its (non-adjacent) producer instead of producing a fabricated sync
        # across the terminal row.
        def _when_parts(raw: str):
            m = re.match(r"^([A-Za-z]+)[./]([A-Za-z]+)\[([^\]]*)\]\s*$",
                         (raw or "").strip().strip("`"))
            return (m.group(1), m.group(2), m.group(3).strip()) if m else None

        producers = [(r.then_concept, r.then_action,
                      ap.normalize_outcome(r.outcome_base), r) for r in rows]

        for row in rows:
            # A composite `When` (join) resolves EVERY conjunct to its producer
            # and emits one joined sync with all conjuncts in declared order.
            if row.composite_when and row.conjuncts:
                resolved = []
                for c in row.conjuncts:
                    source = _resolve_when_source(
                        c.concept, c.action, c.outcome, producers, row,
                        warnings, fname)
                    if source is None:
                        resolved.append(None)
                        break
                    prev_c, outcome_raw = source
                    resolved.append((c.name, prev_c.then_concept,
                                     prev_c.then_action, outcome_raw,
                                     prev_c.row_num))
                if not resolved or resolved[-1] is None:
                    warnings.append(
                        f"{fname} row {row.row_num}: joined `When` has an "
                        f"unresolved conjunct; skipped")
                    continue
                target_concept, target_action = row.then_concept, row.then_action
                joined = [ap.Conjunct(n, c, a, o)
                          for (n, c, a, o, _rn) in resolved]
                when_sig = " \u2227 ".join(
                    (f"{n}: " if n else "")
                    + f"{c}/{a}: [...] => [ {ap.first_completion_token(o)} ]"
                    for (n, c, a, o, _rn) in resolved)
                first = resolved[0]
                syncs.append(GeneratedSync(
                    name="",
                    stem="",
                    trigger_concept=first[1],
                    trigger_action=first[2],
                    trigger_completion=completion_with_payload(first[3]),
                    target_concept=target_concept,
                    target_action=target_action,
                    source_row="+".join(str(rn) for *_x, rn in resolved),
                    target_row=str(row.row_num),
                    when_sig=when_sig,
                    then_sig=f"{target_concept}/{target_action}: [ <args> ]",
                    literals="<none>",
                    binds=[],
                    pattern_d_notes=[],
                    cited_scenario=scenario,
                    is_join=True,
                    conjuncts=[(n, c, a, o) for (n, c, a, o, _rn) in resolved],
                    trigger_outcome_raw=first[3],
                    flow_route=root_route,
                    flow_method=root_method,
                ))
                continue

            parts = _when_parts(row.when)
            if parts is None:
                continue
            wc, wa, wo = parts
            source = _resolve_when_source(wc, wa, wo, producers, row,
                                          warnings, fname)
            if source is None:
                continue  # root row (Web/request entry) — not a sync
            prev, trigger_outcome_raw = source

            trigger_concept = prev.then_concept
            trigger_action = prev.then_action
            trigger_completion = completion_token(trigger_outcome_raw)

            target_concept = row.then_concept
            target_action = row.then_action

            # R15 route matcher: a `Web/request` bootstrap sync keeps the flow
            # root's route/method as its when-clause input matcher.
            route = method = None
            if trigger_concept == "Web" and trigger_action == "request":
                route, method = root_route, root_method

            source_row_id = str(prev.row_num)
            target_row_id = str(row.row_num)

            if route:
                scope_tokens = f'route: "{route}"'
                if method:
                    scope_tokens += f' ; method: "{method}"'
                when_sig = (f"{trigger_concept}/{trigger_action}: [ {scope_tokens} ] => "
                            f"[ {trigger_outcome_raw} ]")
                literals = (f'route = "{route}"'
                            + (f' ; method = "{method}"' if method else ""))
            else:
                when_sig = (f"{trigger_concept}/{trigger_action}: [...] => "
                            f"[ {trigger_outcome_raw} ]")
                literals = "<none>"
            then_sig = f"{target_concept}/{target_action}: [ <args> ]"

            binds: List[Tuple[str, str, str]] = []
            pattern_d_notes: List[str] = []
            if prev.outcome_payload:
                var = "?" + prev.outcome_payload
                binds.append((var, "A", f"Trigger token (`{trigger_concept}/{trigger_action}`)"))

            syncs.append(GeneratedSync(
                name="",
                stem="",
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
                route=route,
                flow_route=root_route,
                flow_method=root_method,
                method=method,
                trigger_outcome_raw=trigger_outcome_raw,
            ))

    # A sync is defined once, not once per scenario that traverses it. Dedup by
    # EDGE IDENTITY, not by name: grammar-v3 names are concept-free, so two
    # distinct edges may share a short name until escalation (below), and name
    # dedup would wrongly collapse them.
    def _edge_id(g: GeneratedSync):
        if g.is_join:
            return ("join", tuple(g.conjuncts),
                    g.target_concept, g.target_action)
        return ("single", g.trigger_concept, g.trigger_action,
                g.trigger_outcome_raw, g.target_concept, g.target_action)

    # The flow pin: every non-bootstrap rule names its flow root first, with the
    # route matcher, so two use cases sharing a completion cannot fire each
    # other's rules. See maintenance/sync-flow-pinning.md.
    for g in syncs:
        if g.trigger_concept == "Web" and g.trigger_action == "request":
            continue                       # the bootstrap IS the flow root
        if not g.conjuncts:
            # A single-trigger rule carries its trigger in the trigger_* fields,
            # not in `conjuncts`; pinning makes it a join, so the trigger becomes
            # its first conjunct.
            g.conjuncts = [(None, g.trigger_concept, g.trigger_action,
                            g.trigger_completion)]
        g.is_join = True
        # The pin goes LAST. CLAD's engine dispatches a joined rule on its
        # PRIMARY (first) conjunct's completion, so a pin placed first would fire
        # the rule before its own trigger had completed — and never re-evaluate.
        # ConceptBox's `actions([...])` is order-agnostic; its reading order is
        # not transferable (maintenance/sync-flow-pinning.md).
        g.conjuncts = list(g.conjuncts) + [("requested", "Web", "request", "routed")]
        scope = f'route: "{g.flow_route}"' if g.flow_route else "..."
        if g.flow_method:
            scope += f' ; method: "{g.flow_method}"'
        g.when_sig = (g.when_sig
                      + " \u2227 "
                      + f"requested: Web/request: [ {scope} ] => [ Routed ]")

    seen: Dict[tuple, GeneratedSync] = {}
    unique: List[GeneratedSync] = []
    for g in syncs:
        key = _edge_id(g)
        if key not in seen:
            seen[key] = g
            unique.append(g)
        elif g.route and seen[key].route and g.route != seen[key].route:
            # Two route-scoped bootstraps for the SAME edge: one carrier per
            # edge, so the second is dropped. Surface it so the author
            # hand-authors the sibling carrier rather than losing it silently.
            warnings.append(
                f"route-scoped bootstrap for {g.trigger_concept}/"
                f"{g.trigger_action}: two routes share an edge "
                f"({seen[key].route!r} vs {g.route!r}); the second is not "
                f"emitted — author it by hand with a distinct stem")

    # Grammar v3 (maintenance/sync-name-grammar-v3.md): assign the shortest
    # stem that is unique within the pack, escalating by adding concept tokens
    # back only on a genuine collision.
    used: Set[str] = set()
    for g in unique:
        if g.is_join:
            conjuncts = [ap.Conjunct(n, c, a, o)
                         for (n, c, a, o) in g.conjuncts]
        else:
            conjuncts = [ap.Conjunct(None, g.trigger_concept,
                                     g.trigger_action, g.trigger_outcome_raw)]
        # Ladder: level 0..3 (concept tokens added back), then the payload
        # variant of the fullest form as a last resort (two outcomes of one
        # action differing only in payload).
        ladder = ([(lvl, False) for lvl in range(ap.SYNC_STEM_MAX_LEVEL + 1)]
                  + [(ap.SYNC_STEM_MAX_LEVEL, True)])
        chosen = None
        # The pin is in every non-bootstrap rule and so names nothing.
        stem_conjuncts = (conjuncts[:-1]
                          if conjuncts and conjuncts[-1].name == "requested"
                          else conjuncts)
        # The name is about what discriminates this rule from its neighbours: a
        # pinned single-trigger rule is named by its trigger, not as a join.
        stem_is_join = len(stem_conjuncts) > 1
        for level, with_payload in ladder:
            candidate = ap.sync_stem(g.target_concept, g.target_action,
                                     stem_conjuncts, stem_is_join, level, with_payload,
                                     route=getattr(g, "route", ""))
            if candidate not in used:
                chosen = candidate
                break
        if chosen is None:
            level, with_payload = ladder[-1]
            chosen = ap.sync_stem(g.target_concept, g.target_action,
                                  stem_conjuncts, stem_is_join, level, with_payload,
                                  route=getattr(g, "route", ""))
            warnings.append(
                f"{chosen}: stem still collides at max escalation; "
                f"author it by hand with a distinct stem")
        g.stem = chosen
        g.name = chosen
        used.add(chosen)
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
    if g.is_join and g.conjuncts:
        for index, (name, concept, action, outcome_raw) in enumerate(g.conjuncts):
            prefix = f"{name}: " if name else ""
            if index == len(g.conjuncts) - 1 and g.flow_route:
                scope = f'route: "{g.flow_route}"'
                if g.flow_method:
                    scope += f' ; method: "{g.flow_method}"'
                lines.append(
                    f"    {prefix}{concept}/{action}: [ {scope} ] => "
                    f"[ {ap.first_completion_token(outcome_raw)} ; ... ]")
                continue
            lines.append(
                f"    {prefix}{concept}/{action}: [ ... ] => "
                f"[ {ap.first_completion_token(outcome_raw)} ; ... ]")
    else:
        if g.route:
            scope_tokens = f'route: "{g.route}"'
            if g.method:
                scope_tokens += f' ; method: "{g.method}"'
            when_cell = f"[ {scope_tokens} ]"
        else:
            when_cell = "[ ... ]"
        lines.append(f"    {g.trigger_concept}/{g.trigger_action}: {when_cell} => [ {g.trigger_completion} ; ... ]")
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
