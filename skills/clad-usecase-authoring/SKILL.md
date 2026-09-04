---
name: clad-usecase-authoring
description: Write a use case specification during CLAD Stage 01. Use when producing usecase.md for a feature, defining operational principle, actors, named scenarios with triggers, preconditions, and postconditions.
---

# CLAD Use Case Authoring (Stage 01)

> **Role:** required stage guidance for Stage 01. The stage `CONTEXT.md` `Inputs` table is authoritative for *which files to load*; load those exactly. This skill adds working process only and must not cause you to reload documents the contract already named.

## What this skill covers

Producing a use case specification that defines one feature's actors,
trigger, preconditions, postconditions, and named scenarios. This is
the entry point for every per-goal feature folder.

## Files

Stage 01 `Inputs` names `methodology/core/CLAD.md`, `templates/usecase.md`, and the 00 goals. Nothing further is required.

## Process

1. Open the approved goal from Stage 00.
2. Derive the operational principle, actors, and scenarios.
3. Write `output/usecase.md` following the template.
4. Self-audit: run `python3 quality-gate/verify_artefacts.py` and fix any defects.
5. Stop at the gate.

## Hard constraints

- Every scenario must have a trigger and a distinct user goal.
- The use case defines *what* the system must do, not *how*.
- Postconditions describe observable state after scenario completion.
