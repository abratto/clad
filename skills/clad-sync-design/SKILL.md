---
name: clad-sync-design
description: Design declarative synchronization rules during CLAD Stage 03. Use when authoring *.sync.md files, building Sync Contract Matrices, and applying the four data-flow patterns (A/B/C/D) to chain-table transitions.
---

# CLAD Sync Design (Stage 03)

## What this skill covers

Producing one `<name>.sync.md` per coordination rule. Each sync is a
declarative `when → where → then` rule that wires two concept actions.
Syncs are the only place where two concepts come into contact.

## Quick reference

Load these files in order:

1. `methodology/architecture/SYNCHRONIZATIONS.md` — sync shape, must-not-do,
   composition rules
2. `methodology/architecture/SYNC_PATTERNS.md` — the four legal data-flow
   patterns (A, B, C, D)
3. `methodology/architecture/FLOW_TOKENS.md` — token structure and payload rules
4. `templates/sync.md` — output shape with embedded authoring rules
5. `features/UC-XX-<slug>/stages/02b_chain-table/output/` —
   approved chain tables (source of every `when`/`then` edge)
6. `features/UC-XX-<slug>/stages/02_concepts/output/` —
   approved concept specs (action signatures)
7. The current stage `CONTEXT.md` for exact Inputs/Outputs/Process

## Process

1. One sync per chain-table transition — count the row-to-row arrows.
2. Build a Sync Contract Matrix first: source row, target row, exact
   `when`, exact `then`, allowed literals.
3. Add `where` clauses using pattern labels (A/B/C/D).
4. Write the declarative rule block.
5. Add `Cites` referencing the use-case scenario.
6. Stop at the gate.

## Hard constraints

- No imperative branching in syncs (R3).
- Do not collapse two transitions into one sync.
- Every `where` line carries a pattern label.
- Preserve literal identity exactly — no type coercion.
- No invented payload fields.
- `[ refused ]` is matched identically to any other outcome token in
  `when` clauses.
- If a 02b row and 02 concept signature disagree, stop and reopen Stage 02.
