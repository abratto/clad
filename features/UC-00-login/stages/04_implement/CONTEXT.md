# Stage 04 — Implement (router) — UC-00-login

This stage owns no artefacts of its own. It routes to the five sub-stages.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../02_concepts/output/` | 4 | Concept specs |
| `../03_syncs/output/` | 4 | Sync specs |
| `../../../../methodology/implementation/STAGES.md` | 3 | §"Stage 04 — `04_implement/` (router)" |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rules |
| `../../../../reference-impl/java-micronaut-jena/CODE_STYLE.md` | 3 | Java profile conventions |

## Process

Run the sub-stages in order, gating after each:

1. [`04a_orm/`](04a_orm/CONTEXT.md) — not applicable (in-memory profile)
2. [`04b_spec/`](04b_spec/CONTEXT.md) — per-concept SPEC slice
3. [`04c_flow-tests/`](04c_flow-tests/CONTEXT.md) — outer red (flow tests)
4. [`04d_concept-tdd/`](04d_concept-tdd/CONTEXT.md) — inner red→green per concept
5. [`04e_sync-tdd/`](04e_sync-tdd/CONTEXT.md) — inner red→green per sync; outer goes green

## Outputs

(none — see sub-stages)

## Verify

- Every sub-stage has been gated.
- The flow tests from `04c` are green at the end of `04e`.
- **Cross-stage check (back):** every concept in `02_concepts/output/` and every sync in `03_syncs/output/` has a corresponding sub-stage output.

## Gate

Default — fires only after `04e` is green.
