---
name: clad-dependency-review
description: Perform the per-UC coordination review during CLAD Stage 03a. Use when auditing cross-concept coupling, producing coordination-review cards, and consolidating concept-state reads before Stage 04 implementation.
---

# CLAD Coordination Review (Stage 03a)

> **Role:** required stage guidance for Stage 03a — the per-UC **coordination
> review** (the skill name and `03a_dependency-review/` folder are unchanged;
> only the description is). The stage `CONTEXT.md` `Inputs` table is
> authoritative for *which files to load*; load those exactly. This skill adds
> working process only.

## What this skill covers

Producing one `<concept>-card.md` per concept and a `pattern-d-summary.md`.
This is the last cross-concept sanity check before code — making every
inbound call and every concept-state read visible per concept.

The cards are **evidence** for the app-level concept-dependence graph
(`features/_system/concept-dependence.md`), never its source. This stage does
not emit that graph; the graph is a reviewed system-scope artefact.

## Files

Stage 03a `Inputs` names `SYNC_PATTERNS.md`, the card/summary templates, and the 01a/02/03 outputs. The extra `methodology/architecture/ARTEFACT_MAP.md` producer→consumer graph is optional background.

## Process

1. Produce one card per concept in the responsibility map.
2. Section 1: list every sync whose `then` calls an action on this concept.
3. Section 2: list every concept-state read of this concept by other concepts.
4. Shared trigger analysis: consult the cross-UC shared-trigger view
    (`features/_system/shared-triggers.md`, generated) as well as this
    feature's syncs. For each sync, determine whether its trigger
    action can be produced by more than one named flow/route. If yes,
    record in the relevant `*-card.md`:
    - Which routes produce this trigger
    - Whether the sync has a route filter
    - If no filter: explicit justification for why route-agnostic firing
       is correct
5. Produce `pattern-d-summary.md`: one row per concept-state read.
6. Self-audit: run `python3 quality-gate/verify_artefacts.py` and fix any defects.
7. Stop — no new design; only audit.

## Hard constraints

- Copy names exactly from approved Stage 03 syncs — no normalization.
- Token mismatch is a defect to surface, not repair.
- A sync without a route filter on a shared trigger is a dependency
   review finding that must be resolved before Gate 2 unless the card
   documents why route-agnostic firing is correct.
- If a sync name disagrees with 01b or 02, stop and reopen the earlier stage.
