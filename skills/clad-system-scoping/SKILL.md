---
name: clad-system-scoping
description: Identify actors and goals during CLAD Stage 00 (system-level actor/goal analysis). Use when starting a new project brief, conducting collaborative multi-turn scoping, or producing actors.md and goals.md.
---

# CLAD System Scoping (Stage 00)

> **Role:** required stage guidance for Stage 00. The stage `CONTEXT.md` `Inputs` table is authoritative for *which files to load*; load those exactly. This skill adds working process only and must not cause you to reload documents the contract already named.

## What this skill covers

Stage 00 runs once per system brief and is collaborative: the agent
proposes, asks clarifying questions, and writes `actors.md` and
`goals.md` only when the human signals agreement.

## Files

Stage 00 `CONTEXT.md` (the contract) and `templates/actors.md`/`goals.md` are the loading set. Nothing further is required.

## Process

1. Read the human's brief.
2. Propose actors and goals (ask ≤5 clarifying questions).
3. Identify external adapter constraints: ask whether there is an
    existing API contract, published spec, or external test suite that
    the system's HTTP surface must conform to.
    - If yes, obtain the contract document or test files, produce
       `port-spec.md` alongside `actors.md` and `goals.md`, and note in
       `goals.md` that adapter compliance is a system-level constraint.
    - If no, note in `goals.md` that the adapter format is a design
       choice to be made at Stage 04b. Do not produce `port-spec.md`.
4. Iterate until agreement.
5. Write `actors.md`, `goals.md`, and optional `port-spec.md` to
    `features/_system/stages/00_actor-goal/output/`.
6. Self-audit: run `python3 quality-gate/verify_artefacts.py` and fix any defects.
7. Stop at the gate.

## Hard rules

- This stage is **multi-turn** — do not rush to output.
- Outputs go into `features/_system/stages/00_actor-goal/output/`.
- `port-spec.md` is produced only when an external adapter contract
   exists; it is not a use-case artefact.
- Each confirmed in-scope goal becomes a `features/UC-XX-<slug>/` folder
  after this gate passes.
