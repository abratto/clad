# Stage 04 — Implement (router) — UC-00-login

This stage owns no artefacts of its own. It routes to the five sub-stages.

## Why this stage exists

**Outside-in TDD double-loop.** The outer loop is one failing flow
test per use-case scenario (`04c`). The inner loop is per-concept
(`04d`) and per-sync (`04e`) red→green. `04a` and `04b` prepare the
ground (state schema and per-concept SPEC slice). Order matters:
state schema before tests, tests before code, concept code before
sync code, sync code is what turns the outer flow test green.

**Feeds:**

- (this router owns no artefacts — sub-stages do.)
- the running, compilable artefact → Stage 05 (back-trace target + smoke target).

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

## Next stage

→ [`04a_orm/CONTEXT.md`](04a_orm/CONTEXT.md) — ORM (state schema)

For in-memory profiles, skip 04a and go straight to [`04b_spec/CONTEXT.md`](04b_spec/CONTEXT.md). Mark 04a with a `_NOT_APPLICABLE.md` note in its `output/`.

To advance, the human says: **"Proceed to Stage 04a."** (or **"Skip 04a, proceed to 04b."**)
