# Stage 01 — Use case

## Why this stage exists

The use case is the **contract every later artefact compiles against**.
Stages 02a, 02b, 02, 03, 04c and 05 each carry a back-cite to a
scenario in this file. If the Postcondition rigour is skipped here
(especially the *no state is modified* assertion on negative paths),
Stage 04c cannot mechanically check the no-enumeration property and
Stage 05 cannot decide whether an observed runtime trace was correct
or merely plausible. Hence: Fully Dressed, both Postcondition
sub-sections, mandatory.

**Feeds:**

- `usecase.md` → 02a (scenarios drive coverage), 02b (one chain table per scenario), 02 (each concept's operational principle must reference these scenarios), 03 (every sync's `Cites` names a scenario), 04c (one flow test per scenario), 05 (verifier walks each scenario's token tree).

**Agent stance for this stage:** you are writing the source of truth
for everything downstream. Prefer over-specifying postconditions to
under-specifying them.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../00_actor-goal/output/actors.md` | 4 | Confirmed actors |
| `../00_actor-goal/output/goals.md` | 4 | Confirmed goals |
| `../../../../methodology/core/CLAD.md` | 3 | Methodology |
| `../../../../templates/usecase.md` | 3 | Output template |
| `../../_config/voice.md` | 3 | Feature voice |

## Process

Draft `usecase.md` by composing one operational principle paragraph
that covers all in-scope goals from stage 00. List the actors verbatim
from `actors.md`. Write one named scenario per in-scope goal (or per
distinct trigger if a goal has several). Write the out-of-scope
section by lifting out-of-scope goals from `goals.md` and adding any
implicit exclusions.

An optional Mermaid `sequenceDiagram` may be included inside each
scenario as a derived, human-facing interaction sketch. If present, it
must stay actor/system-only and must not introduce concept discovery,
sync design, provenance, or state claims that are not already stated in
the prose scenario.

Default expectation: include the diagram when it materially improves
review clarity, especially for scenarios with branching extensions,
opaque error handling, or more than three interaction steps. Omit it
when it would merely restate a short linear scenario without adding
useful visual structure.

The use case **must be Fully Dressed** before exiting this stage —
the completeness checkbox at the top of `usecase.md` selects "Fully
Dressed", and every scenario carries both `Postconditions — Success`
and `Postconditions — Failure`. See
[`../../../../templates/usecase.md`](../../../../templates/usecase.md)
for level definitions and the rationale.

## Outputs

- `output/usecase.md` — the use case spec (Fully Dressed)

## Verify

- The completeness level is **Fully Dressed**.
- Every scenario has pre-conditions, a main flow, ≥1 observable outcome,
  **and** both `Postconditions — Success` and `Postconditions — Failure`
  sub-sections (the Failure section may say "no state is modified" but
  must be present).
- Any Mermaid `sequenceDiagram` included in the use case is consistent
  with the prose scenario and remains explanatory only; it introduces no
  concept names, sync names, or extra steps absent from the prose.
- Scenarios with branching extensions, opaque failure paths, or longer
  interaction sequences include an interaction sketch unless there is a
  clear reason it would add no review value.
- `Trigger` is present unless the scenario is a straightforward
  actor-initiated flow.
- Out-of-scope section is non-empty.
- The operational principle reads as a coherent story, not a feature list.
- **Cross-stage check (back):** every in-scope goal in
  `00_actor-goal/output/goals.md` corresponds to at least one named
  scenario in `usecase.md`.

## Gate

Default human approval. The use case is the contract every later
stage compiles against; gate carefully.

## Next stage

→ [`../02a_responsibility-map/CONTEXT.md`](../02a_responsibility-map/CONTEXT.md) — Responsibility map

To advance, the human says: **"Proceed to Stage 02a."**
