# Stage 02a — Responsibility map (UC-00-login)

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | UC-00-login scenarios |
| `../00_actor-goal/output/actors.md` | 4 | Cross-stage check |
| `../../../../methodology/architecture/CONCEPTS.md` | 3 | What counts as a concept |
| `../../../../methodology/implementation/RULES.md` | 3 | R1 |
| `../../../../templates/responsibility-map.md` | 3 | Output template |

## Process

Identify the concepts UC-00-login requires. Produce one row per
concept in `output/responsibility-map.md`. Do **not** draft full
specs (Stage 02) and do **not** describe choreography (Stage 02b).

## Outputs

- `output/responsibility-map.md`

## Verify

- One row per concept; one-line state; action names only.
- Every UC-00 actor with an in-scope goal is represented.
- Every UC-00 scenario lists at least one concept; every concept
  appears in at least one scenario.

## Gate

Default human approval. **Do you agree with this step? Any
corrections before I continue?**
