# Stage 01 — Use case

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

## Outputs

- `output/usecase.md` — the use case spec

## Verify

- Every scenario has a trigger, pre-conditions, and ≥1 observable outcome.
- Out-of-scope section is non-empty.
- The operational principle reads as a coherent story, not a feature list.
- **Cross-stage check (back):** every in-scope goal in
  `00_actor-goal/output/goals.md` corresponds to at least one named
  scenario in `usecase.md`.

## Gate

Default human approval. The use case is the contract every later
stage compiles against; gate carefully.
