---
name: clad-handover
description: Hand off or resume a feature mid-flight during a CLAD session. Use when orienting a fresh model session to pick up an in-progress feature without manual stage narration.
---

# CLAD Handover

## What this skill covers

Self-orienting protocol for any fresh model session to pick up a feature
mid-flight. The agent diagnoses the current stage from folder structure,
reads prior artefacts, and waits for human confirmation before proceeding.

## Quick reference

Load these files:

1. `methodology/implementation/HANDOVER.md` — complete handover prompt
   template with `{{UC-XX-slug}}` placeholder
2. `AGENTS.md` — operating principles and contract loop
3. `methodology/implementation/STAGES.md` — stage map
4. `methodology/implementation/DELIVERY.md` — trunk-based workflow

## Process

1. Replace `{{UC-XX-slug}}` with the feature folder name.
2. Read `AGENTS.md`, `STAGES.md`, `DELIVERY.md`, `HANDOVER.md`.
3. Inspect `features/UC-XX-<slug>/stages/` in chronological order —
   current stage is the first with no output artefacts.
4. Read all prior stages' output artefacts.
5. Read `features/UC-XX-<slug>/RESUME.md` for fine-grained state.
6. State out loud: feature, current stage, next task.
7. Wait for explicit human confirmation.

## Hard constraints

- Never write artefacts directly to `main`.
- Stop after stage output and wait for human approval.
- Read `RESUME.md` before writing — it may contain corrections not
  visible from folder structure.
