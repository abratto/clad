---
name: clad-usecase-authoring
description: Write a use case specification during CLAD Stage 01. Use when producing usecase.md for a feature, defining operational principle, actors, named scenarios with triggers, preconditions, and postconditions.
---

# CLAD Use Case Authoring (Stage 01)

## What this skill covers

Producing a use case specification that defines one feature's actors,
trigger, preconditions, postconditions, and named scenarios. This is
the entry point for every per-goal feature folder.

## Quick reference

Load these files in order:

1. `methodology/core/CLAD.md` — CLAD principles and contract loop
2. `templates/usecase.md` — output shape (3 completeness levels: Brief,
   Casual, Fully Dressed)
3. `features/_system/stages/00_actor-goal/output/goals.md` — this
   feature's approved goal
4. The current stage `CONTEXT.md` for exact Inputs/Outputs/Process

## Process

1. Open the approved goal from Stage 00.
2. Derive the operational principle, actors, and scenarios.
3. Write `output/usecase.md` following the template.
4. Stop at the gate.

## Hard constraints

- Every scenario must have a trigger and a distinct user goal.
- The use case defines *what* the system must do, not *how*.
- Postconditions describe observable state after scenario completion.
