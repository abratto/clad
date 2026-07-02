---
name: clad-dependency-review
description: Perform a per-concept dependency review during CLAD Stage 03a. Use when auditing cross-concept coupling, producing dependency review cards, and consolidating Pattern D reads before Stage 04 implementation.
---

# CLAD Dependency Review (Stage 03a)

## What this skill covers

Producing one `<concept>-card.md` per concept and a `pattern-d-summary.md`.
This is the last cross-concept sanity check before code — making every
inbound call and every Pattern D read visible per concept.

## Quick reference

Load these files:

1. `methodology/architecture/SYNC_PATTERNS.md` — the four patterns and
   the rule that D is the only legal cross-concept read
2. `methodology/architecture/ARTEFACT_MAP.md` — producer→consumer
   dependency graph
3. `templates/dependency-review-card.md` — per-concept card template
4. `templates/pattern-d-summary.md` — cross-flow Pattern D summary template
5. `features/UC-XX-<slug>/stages/03_syncs/output/` — every `then`
   invocation and `where` clause
6. The current stage `CONTEXT.md` for exact Inputs/Outputs/Process

## Process

1. Produce one card per concept in the responsibility map.
2. Section 1: list every sync whose `then` calls an action on this concept.
3. Section 2: list every Pattern D read of this concept by other concepts.
4. Shared trigger analysis: for each sync, determine whether its trigger
    action can be produced by more than one named flow/route. If yes,
    record in the relevant `*-card.md`:
    - Which routes produce this trigger
    - Whether the sync has a route filter
    - If no filter: explicit justification for why route-agnostic firing
       is correct
5. Produce `pattern-d-summary.md`: one row per Pattern D read.
6. Stop — no new design; only audit.

## Hard constraints

- Copy names exactly from approved Stage 03 syncs — no normalization.
- Token mismatch is a defect to surface, not repair.
- A sync without a route filter on a shared trigger is a dependency
   review finding that must be resolved before Gate 2 unless the card
   documents why route-agnostic firing is correct.
- If a sync name disagrees with 02b or 02, stop and reopen the earlier stage.
