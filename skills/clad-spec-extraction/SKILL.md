---
name: clad-spec-extraction
description: Extract per-concept SPEC slices during CLAD Stage 04b. Use when mechanically deriving SPEC files from approved concept specs and chain tables, producing action signatures and outcome enums for Stage 04c flow tests.
---

# CLAD SPEC Extraction (Stage 04b)

> **Role:** required stage guidance for Stage 04b. The stage `CONTEXT.md` `Inputs` table is authoritative for *which files to load*; load those exactly. This skill adds working process only and must not cause you to reload documents the contract already named.

## What this skill covers

Mechanically extracting SPEC slices — one `<Name>.spec.md` per concept —
from approved Stage 02 concept specs. SPECs declare action signatures,
outcome enums, and flow-token shapes in a form that Stage 04c flow tests
and Stage 04d concept TDD compile against.

## Files

Stage 04b `Inputs` names `templates/spec.md` and the 02/01b outputs. The extra `WEB_CONCEPT.md` and `ENGINE.md` (bootstrap/runtime shape) are optional background for flow-token shape.

## Process

1. For each concept, extract from its `.concept.md`:
   - Every action name and signature
   - Every outcome name (verbatim from chain tables)
   - The flow-token shape
2. Write `output/<Name>.spec.md` per concept.
3. If `port-spec.md` exists, add a separate **Response shapes** section
   with exact JSON paths, field types, wrappers, and error envelope
   values for each relevant HTTP endpoint.
4. Self-audit: run `python3 quality-gate/verify_artefacts.py` and fix any defects.
5. Auto-advance to Stage 04c.

## Hard constraints

- No new design — SPEC extraction is mechanical.
- Outcome names and action signatures must match the concept spec and
  chain tables exactly.
- When a port spec exists, response-shape assertions are derived only
   from that external contract and stay separate from concept action
   signatures.
