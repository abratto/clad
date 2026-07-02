---
name: clad-spec-extraction
description: Extract per-concept SPEC slices during CLAD Stage 04b. Use when mechanically deriving SPEC files from approved concept specs and chain tables, producing action signatures and outcome enums for Stage 04c flow tests.
---

# CLAD SPEC Extraction (Stage 04b)

## What this skill covers

Mechanically extracting SPEC slices — one `<Name>.spec.md` per concept —
from approved Stage 02 concept specs. SPECs declare action signatures,
outcome enums, and flow-token shapes in a form that Stage 04c flow tests
and Stage 04d concept TDD compile against.

## Quick reference

Load these files:

1. `methodology/architecture/WEB_CONCEPT.md` — bootstrap concept constraints
2. `methodology/architecture/ENGINE.md` — runtime engine shape for flow
   tokens
3. `templates/spec.md` — SPEC slice output shape
4. `features/UC-XX-<slug>/stages/02_concepts/output/` —
   approved concept specs (source)
5. `features/UC-XX-<slug>/stages/02b_chain-table/output/` —
   approved chain tables (outcome names)
6. The current stage `CONTEXT.md` for exact Inputs/Outputs/Process
7. `features/_system/stages/00_actor-goal/output/port-spec.md` — only
   when it exists; external adapter response-shape contract

## Process

1. For each concept, extract from its `.concept.md`:
   - Every action name and signature
   - Every outcome name (verbatim from chain tables)
   - The flow-token shape
2. Write `output/<Name>.spec.md` per concept.
3. If `port-spec.md` exists, add a separate **Response shapes** section
   with exact JSON paths, field types, wrappers, and error envelope
   values for each relevant HTTP endpoint.
4. Auto-advance to Stage 04c.

## Hard constraints

- No new design — SPEC extraction is mechanical.
- Outcome names and action signatures must match the concept spec and
  chain tables exactly.
- When a port spec exists, response-shape assertions are derived only
   from that external contract and stay separate from concept action
   signatures.
