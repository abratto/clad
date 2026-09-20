---
name: clad-responsibility-mapping
description: Derive a responsibility map during CLAD Stage 01a. Use when listing concepts, their owned state, and action names from the approved use case, before writing chain tables or concept specs.
---

# CLAD Responsibility Mapping (Stage 01a)

> **Role:** required stage guidance for Stage 01a. The stage `CONTEXT.md` `Inputs` table is authoritative for *which files to load*; load those exactly. This skill adds working process only and must not cause you to reload documents the contract already named.

## What this skill covers

Producing a responsibility map — one row per concept — listing state, actions,
and a coverage check. This defines the concept set for all downstream stages.

## Files

Stage 01a `Inputs` names `templates/responsibility-map.md`, the 01 use case,
the generated catalog `features/_system/concepts-catalog.md`, and the
app-level graph `features/_system/concept-dependence.md` (the latter two are
conditional — a project's first feature has none).

## Process

1. Identify every concept needed by the use case scenarios.
2. **Consult the vocabulary before deriving.** Check the catalog — it carries
   action names, so you can tell whether the capability and action already
   exist without opening the full spec. Classify each concept's `Origin`:
   - `reused:UC-XX` — concept and actions already canonical; bind, do not
     re-author;
   - `extends:UC-XX` — concept exists but the action/state does not;
   - `new` — otherwise.
3. Assign one row per concept: name, `Origin`, owned state, action names,
   coverage. For every `new`/`extends` row, fill the *Proposals* section
   (proposed addition + any `requires` dependence claim).
4. Produce `output/responsibility-map.md`.
5. Self-audit: run `python3 quality-gate/verify_artefacts.py` and fix any defects.
6. Stop at the gate.

## Hard constraints

- Every concept that will appear in a chain table or concept spec must
  be listed here.
- Do not introduce a concept in a chain table that is absent from this map.
- A `reused` row must not re-author the concept — Stage 02 binds to the
  canonical corpus spec (`features/_system/concepts/`). Reuse is ~90% of
  design; re-deriving a concept per use case is the drift R22 forbids.
