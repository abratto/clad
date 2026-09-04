---
name: clad-concept-design
description: Design a business concept specification during CLAD Stage 02. Use when authoring a *.concept.md file, defining concept state (Alloy notation), actions (case-split), and operational principle under WYSIWID architecture.
---

# CLAD Concept Design (Stage 02)

> **Role:** required stage guidance for Stage 02. The stage `CONTEXT.md`
> `Inputs` table is authoritative for *which files to load*; load those
> exactly. This skill adds the working process only.

## What this skill covers

Producing one `<Name>.concept.md` per business concept. Each spec defines
the concept's private state, public actions with case-split outcomes, and
an operational principle trace.

## Files

The stage `CONTEXT.md` `Inputs` names the loading set: `01b` chain tables,
`CONCEPTS.md`, `templates/concept.md`. The one additional reference worth
having open is `methodology/architecture/LEGIBLE.md` (WYSIWID constraints)
and `MENTAL_MODEL.md` (OO ↔ WYSIWID translation).

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
5. Self-audit: run `python3 quality-gate/verify_artefacts.py` and fix any defects.
6. Stop at the gate.

## Hard rules

- No concept spec mentions another concept's state by name (R1).
- One named graph per concept (R2).
- Every action emits a flow token (R5).
- Web is the sole bootstrap concept (R4).
- Outcome names must match the approved chain table verbatim — no renames.
