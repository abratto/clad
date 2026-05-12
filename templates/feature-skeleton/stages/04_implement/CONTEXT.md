# Stage 04 — Implement (router)

This stage owns no artefacts of its own. It routes to five sub-stages
that together realise the outside-in TDD double-loop.

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

## Process

Run the sub-stages **strictly in order**, gating after each. Before
starting any sub-stage, verify its pre-condition is met. If it is not,
stop and tell the human which earlier sub-stage must be completed first.

| # | Sub-stage | Pre-condition before starting |
|---|---|---|
| 1 | [`04a_orm/`](04a_orm/CONTEXT.md) — optional state model | None (first sub-stage) |
| 2 | [`04b_spec/`](04b_spec/CONTEXT.md) — per-concept SPEC slice | `04a_orm/output/` exists (or `_NOT_APPLICABLE.md` present) |
| 3 | [`04c_flow-tests/`](04c_flow-tests/CONTEXT.md) — outer red (flow tests) | `04b_spec/output/` is non-empty |
| 4 | [`04d_concept-tdd/`](04d_concept-tdd/CONTEXT.md) — inner red→green per concept | `04c_flow-tests/output/` is non-empty |
| 5 | [`04e_sync-tdd/`](04e_sync-tdd/CONTEXT.md) — inner red→green per sync; outer goes green | All concept tests from `04d` are green |

**Do not skip or reorder sub-stages.** The fast-path exception in
`STAGES.md` §"Fast-path" applies only when all four listed conditions
hold; when in doubt, use one-stage-per-turn.

## Outputs

(none — sub-stages own all artefacts)

## Verify

- Every sub-stage has been gated.
- The flow tests from `04c` are green at the end of `04e`.
- **Cross-stage check (back):** every concept and every sync from
  stages 02 and 03 has a corresponding sub-stage output.

## Gate

Default — but the gate fires only after `04e` is green.

## Next stage

→ [`04a_orm/CONTEXT.md`](04a_orm/CONTEXT.md) — ORM (state schema)

For in-memory profiles, skip 04a and go straight to [`04b_spec/CONTEXT.md`](04b_spec/CONTEXT.md). Mark 04a with a `_NOT_APPLICABLE.md` note in its `output/`.

To advance, the human says: **"Proceed to Stage 04a."** (or **"Skip 04a, proceed to 04b."**)
