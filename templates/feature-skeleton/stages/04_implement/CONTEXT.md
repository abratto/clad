# Stage 04 — Implement (router)

This stage owns no artefacts of its own. It routes to five top-level
sub-stages; `04d` and `04e` are themselves routers with structural
red/green child stages.

## Why this stage exists

**Outside-in TDD double-loop.** The outer loop is one failing flow
test per use-case scenario (`04c`). The inner loop is per-concept
(`04d-red` -> `04d-green`) and per-sync (`04e-red` -> `04e-green`).
`04a` and `04b` prepare the ground (state schema and per-concept SPEC
slice). Order matters: state schema before tests, tests before code,
concept code before sync code, sync code is what turns the outer flow
test green.

Stage 04 is the **executable implementation stage**. The markdown
derivation files produced in `04b`/`04c`/`04d-red`/`04e-red` are
supporting artefacts, not substitutes for code or tests. A Stage 04
sub-stage is not complete unless its required side effects exist in the
selected profile and the required commands have been executed for that
sub-stage.

**Feeds:**

- (this router owns no artefacts — sub-stages do.)
- the running, compilable artefact -> Stage 05 (back-trace target + smoke target).

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../02_concepts/output/` | 4 | Concept specs |
| `../03_syncs/output/` | 4 | Sync specs |
| `../../../../methodology/implementation/STAGES.md` | 3 | Stage 04 routing contract |
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
| 4 | [`04d_concept-tdd/`](04d_concept-tdd/CONTEXT.md) — router for `04d_red-tests/` then `04d_green-impl/` | `04c_flow-tests/output/` is non-empty |
| 5 | [`04e_sync-tdd/`](04e_sync-tdd/CONTEXT.md) — router for `04e_red-tests/` then `04e_green-impl/` | All concept tests from `04d_green` are green |

**Do not skip or reorder sub-stages.** The fast-path exception in
`STAGES.md` applies only when all listed conditions hold; when in
doubt, use one-stage-per-turn.

## Outputs

(none — sub-stages own all artefacts)

## Verify

- Every sub-stage has been gated.
- `04b` exists before any `04c`/`04d`/`04e` work.
- `04d_red-tests/` is approved before `04d_green-impl/` starts.
- `04e_red-tests/` is approved before `04e_green-impl/` starts.
- No sub-stage is treated as complete from markdown outputs alone; each
  required code/test side effect exists for the selected profile.
- The flow tests from `04c` are green at the end of `04e_green`.
- **Cross-stage check (back):** every concept and every sync from
  stages 02 and 03 has a corresponding sub-stage output.

## Gate

Default — but the gate fires only after `04e_green-impl/` is green.

## Next stage

-> [`04a_orm/CONTEXT.md`](04a_orm/CONTEXT.md) — ORM (state schema)

For in-memory profiles, skip 04a and go straight to [`04b_spec/CONTEXT.md`](04b_spec/CONTEXT.md). Mark 04a with a `_NOT_APPLICABLE.md` note in its `output/`.

To advance, the human says: **"Proceed to Stage 04a."** (or **"Skip 04a, proceed to 04b."**)
