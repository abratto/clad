# Stage 01 — Use case

## Inputs

| Path | Layer | Why |
|---|---|---|
| (the human's request) | — | Source of intent |
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
