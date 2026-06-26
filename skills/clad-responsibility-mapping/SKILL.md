---
name: clad-responsibility-mapping
description: Derive a responsibility map during CLAD Stage 02a. Use when listing concepts, their owned state, and action names from the approved use case, before writing chain tables or concept specs.
---

# CLAD Responsibility Mapping (Stage 02a)

## What this skill covers

Producing a responsibility map — one row per concept — listing state, actions,
and a coverage check. This defines the concept set for all downstream stages.

## Quick reference

Load these files:

1. `templates/responsibility-map.md` — output shape
2. `features/UC-XX-<slug>/stages/01_usecase/output/usecase.md` —
   the approved use case this map derives from
3. The current stage `CONTEXT.md` for exact Inputs/Outputs/Process

## Process

1. Identify every concept needed by the use case scenarios.
2. Assign one row per concept: name, owned state, action names, coverage.
3. Produce `output/responsibility-map.md`.
4. Stop at the gate.

## Hard constraints

- Every concept that will appear in a chain table or concept spec must
  be listed here.
- Do not introduce a concept in a chain table that is absent from this map.
