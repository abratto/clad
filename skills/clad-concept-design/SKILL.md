---
name: clad-concept-design
description: Design a business concept specification during CLAD Stage 02. Use when authoring a *.concept.md file, defining concept state (Alloy notation), actions (case-split), and operational principle under WYSIWID architecture.
---

# CLAD Concept Design (Stage 02)

> **Role:** required stage guidance for Stage 02. The stage `CONTEXT.md`
> `Inputs` table is authoritative for *which files to load*; load those
> exactly. This skill adds the working process only.

## What this skill covers

Producing a `<Name>.concept.md` for a concept this feature REUSES, EXTENDS,
or NEWLY proposes. Each spec defines the concept's private state, public
actions with case-split outcomes, and an operational principle trace.

**System-scope model (R22).** Concepts are canonical assets: the canonical
spec lives once at `features/_system/concepts/<Name>.concept.md`. This stage
does one of two things per concept, driven by the responsibility map's
`Origin` column:

- **`reused:UC-XX`** — emit a binding row only (`concept-bindings.md`); do
  **not** author a spec copy. The corpus spec is the source of truth.
- **`new` / `extends:UC-XX`** — author a PROPOSAL `<Name>.concept.md` in this
  feature's output. It is promoted into the corpus on Gate 2 approval
  (`./clad promote-concepts`), never by hand. An `extends` proposal must be
  additive — never rename or remove an existing outcome or parameter.

The feature always emits `concept-bindings.md`, even when it reuses
everything and proposes nothing.

## Files

The stage `CONTEXT.md` `Inputs` names the loading set: `01b` chain tables,
`CONCEPTS.md`, `templates/concept.md`. The one additional reference worth
having open is `methodology/architecture/LEGIBLE.md` (WYSIWID constraints)
and `MENTAL_MODEL.md` (OO ↔ WYSIWID translation).

## Process

1. Read the responsibility map's `Origin` per concept, then: REUSE → binding
   row only; NEW/EXTEND → `concept-bindings.md` row **and** a full
   `<Name>.concept.md` proposal.
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
