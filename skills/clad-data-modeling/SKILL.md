---
name: clad-data-modeling
description: Produce conceptual data models during CLAD Stage 03b. Use when applying the CSDP 7-step procedure to derive profile-neutral data models from concept specs and coordination review cards.
---

# CLAD Data Modeling (Stage 03b)

> **Role:** required stage guidance for Stage 03b. The stage `CONTEXT.md` `Inputs` table is authoritative for *which files to load*; load those exactly. This skill adds working process only and must not cause you to reload documents the contract already named.

## What this skill covers

Producing one `<Name>.data-model.md` per **state-owning** concept using the CSDP
(Conceptual Schema Design Procedure) 7-step method. These are
profile-neutral — they describe what data exists, not how it's stored. When no
concept this feature binds changes state (a read-only / binding-only feature),
Stage 03b produces no output and is satisfied as a no-op — do not author a
placeholder data-model.

## Files

Stage 03b `Inputs` names `DATA_MODEL_NOTES.md`, `templates/data-model.md`, and the 02/03a outputs. Nothing further is required.

## Process

1. For each state-owning concept, walk the CSDP 7 steps from concept state.
2. Derive fact types, uniqueness constraints, and reference schemes.
3. Produce one `output/<Name>.data-model.md` per state-owning concept; produce
   none when no concept changes state (read-only feature — 03b is a no-op).
4. Self-audit: run `python3 quality-gate/verify_artefacts.py` and fix any defects.
5. Auto-advance to Stage 04.

## Hard constraints

- Profile-neutral — do not assume RDF, SQL, or document storage.
- Every field from the concept state must appear in the data model.
