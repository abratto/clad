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

Draft the use case for UC-00-login. Identify actors and the named
scenarios the feature must satisfy. One paragraph for the operational
principle. Each scenario is a trigger + expected outcomes. Be honest
about what is out of scope.

## Outputs

- `output/usecase.md` — the use case spec

## Verify

- Every scenario has a trigger, pre-conditions, and at least one
  observable outcome.
- Out-of-scope section is non-empty.
- The operational principle reads as a coherent story, not a feature
  list.
- **Cross-stage check (back):** every in-scope goal in
  `../00_actor-goal/output/goals.md` corresponds to at least one named
  scenario in `usecase.md`.

## Gate

Default human approval. The use case is the contract every later
stage compiles against; gate carefully.
