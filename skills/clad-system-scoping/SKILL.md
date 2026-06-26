---
name: clad-system-scoping
description: Identify actors and goals during CLAD Stage 00 (system-level actor/goal analysis). Use when starting a new project brief, conducting collaborative multi-turn scoping, or producing actors.md and goals.md.
---

# CLAD System Scoping (Stage 00)

## What this skill covers

Stage 00 runs once per system brief and is collaborative: the agent
proposes, asks clarifying questions, and writes `actors.md` and
`goals.md` only when the human signals agreement.

## Quick reference

Load these files:

1. `features/_system/stages/00_actor-goal/CONTEXT.md` — the stage
   contract that governs this work
2. `templates/actors.md` — output shape for actors
3. `templates/goals.md` — output shape for goals

## Process

1. Read the human's brief.
2. Propose actors and goals (ask ≤5 clarifying questions).
3. Iterate until agreement.
4. Write `actors.md` and `goals.md` to `features/_system/stages/00_actor-goal/output/`.
5. Stop at the gate.

## Hard rules

- This stage is **multi-turn** — do not rush to output.
- Outputs go into `features/_system/stages/00_actor-goal/output/`.
- Each confirmed in-scope goal becomes a `features/UC-XX-<slug>/` folder
  after this gate passes.
