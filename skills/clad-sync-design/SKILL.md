---
name: clad-sync-design
description: Design declarative synchronization rules during CLAD Stage 03. Use when authoring *.sync.md files, building Sync Contract Matrices, and applying the four data-flow patterns (A/B/C/D) to chain-table transitions.
---

# CLAD Sync Design (Stage 03)

> **Role:** required stage guidance for Stage 03. The stage `CONTEXT.md`
> `Inputs` table is authoritative for *which files to load*; load those
> exactly. This skill adds the working process only — it must not cause
> you to reload documents the contract already named.

## What this skill covers

Producing one `<name>.sync.md` per coordination rule. Each sync is a
declarative `when → where → then` rule that wires two concept actions.
Syncs are the only place where two concepts come into contact.

## Files

The stage `CONTEXT.md` `Inputs` names the loading order: `01b` chain
tables, `concept-bindings.md` + the canonical concept specs
(`features/_system/concepts/`) and any `02` proposals,
`features/_system/shared-triggers.md`, `SYNCHRONIZATIONS.md`, `SYNC_PATTERNS.md`,
`templates/sync.md`. The one additional reference worth having open is
`methodology/architecture/FLOW_TOKENS.md` (token structure/payload rules).

## Process

1. One sync per chain-table transition — count the row-to-row arrows.
2. Build a Sync Contract Matrix first: source row, target row, exact
   `when`, exact `then`, allowed literals.
3. Add `where` clauses using pattern labels (A/B/C/D).
4. Write the declarative rule block.
5. Add `Cites` referencing the use-case scenario.
6. Self-audit: run `python3 quality-gate/verify_artefacts.py` and fix any defects.
7. Stop at the gate.

## Which subset do I need

Match the chain-table row in front of you and add only the level it needs.

- **Level 0 — bootstrap row.** `when Web/request … then <Concept>/<action>`;
  add `where { bind ( uuid() as ?id ) }` when the row mints an entity. Most rows.
- **Level 1 — a value never in this flow.** Add a `where` concept-state read
  (Pattern D) only when the argument was not carried by the trigger or a sibling.
- **Level 2 — matching ≥2 completions.** Add named-conjunct joins.
- **Level 3 — the flow is shared / the result is a set / the match is an
  absence.** Add flow pinning, `collect`/`collectBy`, or `absent`.

**A/B vs. D — the one choice that matters:** reuse a flow binding (A/B) when the
value already travelled this flow; read concept state (D) only when the value was
never in this flow. D is a real cross-boundary read and the Stage 03a audit will
flag it.

## Translating from paper / ConceptBox examples

> The sources order and phrase things differently; a verbatim translation can
> fire with blank arguments or bypass the audit.

- **Request-first (paper) / order-agnostic (`actions([...])`, ConceptBox) → pin last.** CLAD evaluates a rule's `where` against its primary (**first**) conjunct, so the flow pin is the **final** conjunct.
- **`frames.filter(...)` (ConceptBox) → a concept action outcome** (business discrimination belongs in the concept, R3).
- **`collectAs` (ConceptBox) → `collect` / `collect by ?key`** for a single binding; a correlated multi-binding record has no declarative CLAD form today.
- **Nested `body:` in `then` → the primary adapter** (`verify_sync_then_shape.py` enforces the flat `then`).

## Hard constraints

- No imperative branching in syncs (R3).
- Do not collapse two transitions into one sync.
- Every `where` line carries a pattern label.
- Preserve literal identity exactly — no type coercion.
- No invented payload fields.
- `[ refused ]` is matched identically to any other outcome token in
  `when` clauses.
- If a 01b row and 02 concept signature disagree, stop and reopen Stage 02.
