---
name: clad-handover
description: Hand off or resume a feature mid-flight during a CLAD session. Use when orienting a fresh model session to pick up an in-progress feature without manual stage narration.
---

# CLAD Handover

> **Role:** session-start aggregator. Orient a fresh session from
> `AGENTS.md`, `CONTEXT.md`, `HANDOVER.md` and the feature `RESUME.md` —
> it is not tied to a single stage.

## What this skill covers

Self-orienting protocol for any fresh model session to pick up a feature
mid-flight. The agent diagnoses the current stage from folder structure,
reads prior artefacts, and waits for human confirmation before proceeding.

## Quick reference

The critical orientation files are `methodology/implementation/HANDOVER.md`
(full handover-prompt template), `AGENTS.md` §1–2, and the feature's
`RESUME.md`. The rest of the load order is deterministic from folder state.

## Process

1. Replace `{{UC-XX-slug}}` with the feature folder name.
2. Read `AGENTS.md`, `STAGES.md`, `DELIVERY.md`, `HANDOVER.md`.
3. Inspect `features/UC-XX-<slug>/stages/` in chronological order —
   current stage is the first with no output artefacts.
4. Read all prior stages' output artefacts.
5. Read `features/UC-XX-<slug>/RESUME.md` for fine-grained state.
6. Run `python3 quality-gate/advance.py --feature features/UC-XX-<slug>`
   to validate the pipeline state and identify the next action.
7. State out loud: feature, current stage, next task.
8. Wait for explicit human confirmation.

## Hard constraints

- Never write artefacts directly to `main`.
- Stop after stage output and wait for human approval.
- Read `RESUME.md` before writing — it may contain corrections not
  visible from folder structure.
