# Stage 04 — Implement (router)

This stage owns no artefacts of its own. It routes to five sub-stages
that together realise the outside-in TDD double-loop.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../02_concepts/output/` | 4 | Concept specs |
| `../03_syncs/output/` | 4 | Sync specs |
| `../../../../methodology/implementation/STAGES.md` | 3 | §"Stage 04 — `04_implement/` (router)" |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rules |

## Process

Run the sub-stages in order, gating after each:

1. [`04a_orm/`](04a_orm/CONTEXT.md) — optional state model
2. [`04b_spec/`](04b_spec/CONTEXT.md) — per-concept SPEC slice
3. [`04c_flow-tests/`](04c_flow-tests/CONTEXT.md) — outer red (flow tests)
4. [`04d_concept-tdd/`](04d_concept-tdd/CONTEXT.md) — inner red→green per concept
5. [`04e_sync-tdd/`](04e_sync-tdd/CONTEXT.md) — inner red→green per sync; outer goes green

## Outputs

(none — sub-stages own all artefacts)

## Verify

- Every sub-stage has been gated.
- The flow tests from `04c` are green at the end of `04e`.
- **Cross-stage check (back):** every concept and every sync from
  stages 02 and 03 has a corresponding sub-stage output.

## Gate

Default — but the gate fires only after `04e` is green.
