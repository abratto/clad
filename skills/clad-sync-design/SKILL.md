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
tables, `02` concept specs, `SYNCHRONIZATIONS.md`, `SYNC_PATTERNS.md`,
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

## Hard constraints

- No imperative branching in syncs (R3).
- Do not collapse two transitions into one sync.
- Every `where` line carries a pattern label.
- Preserve literal identity exactly — no type coercion.
- No invented payload fields.
- `[ refused ]` is matched identically to any other outcome token in
  `when` clauses.
- If a 01b row and 02 concept signature disagree, stop and reopen Stage 02.
