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
