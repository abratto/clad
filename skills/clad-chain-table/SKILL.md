---
name: clad-chain-table
description: Derive chain tables during CLAD Stage 01b. Use when translating use case scenarios into numbered When/Then action choreography tables and FSM diagrams, bridging to Stage 03 sync authoring.
---

# CLAD Chain Table Derivation (Stage 01b)

> **Role:** required stage guidance for Stage 01b. The stage `CONTEXT.md` `Inputs` table is authoritative for *which files to load*; load those exactly. This skill adds working process only and must not cause you to reload documents the contract already named.

## What this skill covers

Producing one `<scenario>-chain.md` per use-case scenario. Each chain
table is a numbered `When → Then` action choreography with Inputs,
Outcome, and Why columns, plus a derived Mermaid FSM diagram.

## Files

Stage 01b `Inputs` names `SYNCHRONIZATIONS.md`, `templates/chain-table.md`, and the 01/01a outputs. Nothing further is required.

## Process

1. For each named scenario in the use case, produce one chain-table file.
2. First row: `Web.handle`. Last row: `Web.respond`.
3. One transition branch per row — do not collapse multiple derived
   arrows into one canonical table row.
4. Derive the Mermaid `stateDiagram-v2` mechanically from the table.
5. Self-audit: run `python3 quality-gate/verify_artefacts.py` and fix any defects.
6. Stop at the gate.

## Hard constraints

- One file per top-level Stage 01 scenario.
- First row = `Web.handle`, last row = `Web.respond`.
- Every `Then` concept must be listed in the responsibility map.
- The table and diagram must be presented in the same turn.
