---
name: clad-data-modeling
description: Produce conceptual data models during CLAD Stage 03b. Use when applying the CSDP 7-step procedure to derive profile-neutral data models from concept specs and dependency review cards.
---

# CLAD Data Modeling (Stage 03b)

## What this skill covers

Producing one `<Name>.data-model.md` per concept using the CSDP
(Conceptual Schema Design Procedure) 7-step method. These are
profile-neutral — they describe what data exists, not how it's stored.

## Quick reference

Load these files:

1. `methodology/architecture/DATA_MODEL_NOTES.md` — CSDP 7-step
   procedure and data-model anatomy
2. `templates/data-model.md` — output shape
3. `features/UC-XX-<slug>/stages/02_concepts/output/` —
   concept state definitions
4. `features/UC-XX-<slug>/stages/03a_dependency-review/output/` —
   Pattern D reads drive data-model coverage
5. The current stage `CONTEXT.md` for exact Inputs/Outputs/Process

## Process

1. For each concept, walk the CSDP 7 steps from concept state.
2. Derive fact types, uniqueness constraints, and reference schemes.
3. Produce one `output/<Name>.data-model.md` per concept.
4. Auto-advance to Stage 04.

## Hard constraints

- Profile-neutral — do not assume RDF, SQL, or document storage.
- Every field from the concept state must appear in the data model.
