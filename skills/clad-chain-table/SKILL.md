---
name: clad-chain-table
description: Derive chain tables during CLAD Stage 02b. Use when translating use case scenarios into numbered When/Then action choreography tables and FSM diagrams, bridging to Stage 03 sync authoring.
---

# CLAD Chain Table Derivation (Stage 02b)

## What this skill covers

Producing one `<scenario>-chain.md` per use-case scenario. Each chain
table is a numbered `When → Then` action choreography with Inputs,
Outcome, and Why columns, plus a derived Mermaid FSM diagram.

## Quick reference

Load these files:

1. `methodology/architecture/SYNCHRONIZATIONS.md` — how chains feed syncs
2. `templates/chain-table.md` — output shape, derivation rules, FSM
   diagram mechanics
3. `features/UC-XX-<slug>/stages/01_usecase/output/usecase.md` —
   source scenarios
4. `features/UC-XX-<slug>/stages/02a_responsibility-map/output/responsibility-map.md` —
   the concept set
5. The current stage `CONTEXT.md` for exact Inputs/Outputs/Process

## Process

1. For each named scenario in the use case, produce one chain-table file.
2. First row: `Web.handle`. Last row: `Web.respond`.
3. One transition branch per row — do not collapse multiple derived
   arrows into one canonical table row.
4. Derive the Mermaid `stateDiagram-v2` mechanically from the table.
5. Stop at the gate.

## Hard constraints

- One file per top-level Stage 01 scenario.
- First row = `Web.handle`, last row = `Web.respond`.
- Every `Then` concept must be listed in the responsibility map.
- The table and diagram must be presented in the same turn.
