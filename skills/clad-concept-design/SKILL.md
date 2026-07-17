---
name: clad-concept-design
description: Design a business concept specification during CLAD Stage 02. Use when authoring a *.concept.md file, defining concept state (Alloy notation), actions (case-split), and operational principle under WYSIWID architecture.
---

# CLAD Concept Design (Stage 02)

## What this skill covers

Producing one `<Name>.concept.md` per business concept. Each spec defines
the concept's private state, public actions with case-split outcomes, and
an operational principle trace.

## Quick reference

Load these files in order:

1. `methodology/architecture/LEGIBLE.md` — WYSIWID pattern constraints
2. `methodology/architecture/CONCEPTS.md` — concept anatomy (state, actions,
   operational principle)
3. `methodology/architecture/MENTAL_MODEL.md` — OO ↔ WYSIWID translation
4. `templates/concept.md` — output shape to follow
5. `features/UC-XX-<slug>/stages/02b_chain-table/output/` —
   approved chain tables (outcomes must match exactly)
6. The current stage `CONTEXT.md` for exact Inputs/Outputs/Process

## Process

1. For each concept in the responsibility map, produce one `.concept.md`.
2. State: Alloy-style relational notation with multiplicity annotations.
3. Actions: case-split notation — one block per outcome.
   - **Format A (precondition/postcondition):** Use for actions whose
     failures are pure state-guard violations (e.g. lookup not found).
     Precondition failures cause refusal — the concept writes `:outcome
     "refused"` and syncs match on `[ refused ]`.
   - **Format B (case-split outcomes):** Use for actions whose failure
     pathways still mutate state (e.g. incrementing a counter). Each
     failure is a named `[ error: "..." ]` outcome.
4. Operational principle: a single witness trace in `after`/`then` notation.
5. Stop at the gate.

## Hard rules

- No concept spec mentions another concept's state by name (R1).
- One named graph per concept (R2).
- Every action emits a flow token (R5).
- Web is the sole bootstrap concept (R4).
- Outcome names must match the approved chain table verbatim — no renames.
