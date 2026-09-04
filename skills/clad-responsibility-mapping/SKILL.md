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

Stage 01a `Inputs` names `templates/responsibility-map.md` and the 01 use case. Nothing further is required.

## Process

1. Identify every concept needed by the use case scenarios.
2. Assign one row per concept: name, owned state, action names, coverage.
3. Produce `output/responsibility-map.md`.
4. Self-audit: run `python3 quality-gate/verify_artefacts.py` and fix any defects.
5. Stop at the gate.

## Hard constraints

- Every concept that will appear in a chain table or concept spec must
  be listed here.
- Do not introduce a concept in a chain table that is absent from this map.
