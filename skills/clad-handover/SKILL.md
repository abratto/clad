---
name: clad-handover
description: Hand off, resume, or orchestrate a CLAD feature mid-flight. Use when orienting a fresh model session to pick up an in-progress feature, or when running one sub-agent per stage without manual stage narration.
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
3. Run `./clad advance` — it owns the transition decision and names the
   current/next stage. Do **not** diagnose the stage yourself from folder
   order; run advance even if you think you know where you are.
4. Read all prior stages' output artefacts in chronological order.
5. Read `features/UC-XX-<slug>/RESUME.md` for fine-grained state.
6. State out loud: feature, current stage, next task.
7. Wait for explicit human confirmation (or, for an auto-advance stage,
   proceed to produce its Outputs).

## Recommended: one sub-agent per stage (orchestrators)

If the harness can spawn sub-agents, the **default** way to walk a feature is
**one sub-agent per stage, each driving `./clad advance`**:

1. The parent session is the orchestrator. It runs `./clad advance`, then
   spawns one sub-agent for the named stage with the `HANDOVER.md` block
   (slug substituted) as the mission.
2. The sub-agent loads only the stage `Inputs`, produces the `Outputs`, runs
   the stage `## Verify` + `./clad verify`, and **ends its turn with
   `./clad advance`**.
3. On `NEXT STAGE`, the parent spawns the next stage's sub-agent. At a human
   gate (exit `10`), the sub-agent returns and the parent/human approves with
   `./clad approve <N>` before continuing.

The producing sub-agent runs `advance` at the end of its turn; the next
sub-agent re-runs it on entry as idempotent confirmation. Full loop and the
no-sub-agent fallback: `STAGES.md` §"Orchestration: one sub-agent per stage".

## Hard constraints

- Never write artefacts directly to `main`.
- Stop after stage output and wait for human approval (at gates); stages
  between gates auto-advance via `./clad advance`.
- Never self-select a stage or open a `CONTEXT.md` `advance` did not print.
- A sub-agent never runs `approve_gate.py`; approval stays with the human.
- Read `RESUME.md` before writing — it may contain corrections not
  visible from folder structure.
