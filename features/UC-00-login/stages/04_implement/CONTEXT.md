# Stage 04 — Implement (router) — UC-00-login

This stage owns no artefacts of its own. It routes to five top-level
sub-stages; `04d` and `04e` are themselves routers with structural
red/green child stages.

## Why this stage exists

**Outside-in TDD double-loop.** The outer loop is one failing flow
test per use-case scenario (`04c`). The inner loop is per-concept
(`04d-red` -> `04d-green`) and per-sync (`04e-red` -> `04e-green`).
`04a` and `04b` prepare the ground (storage mapping and per-concept
SPEC slice). Order matters: storage mapping before tests when a
persistent store exists, tests before code, concept code before sync
code, sync code is what turns the outer flow test green.

**Feeds:**

- (this router owns no artefacts — sub-stages do.)
- the running, compilable artefact -> Stage 05 (back-trace target + smoke target).

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../03b_data-model/output/` | 4 | Approved conceptual data models |
| `../02_concepts/output/` | 4 | Concept specs |
| `../03_syncs/output/` | 4 | Sync specs |
| `../../../../methodology/core/ITERATIVE_CHANGES.md` | 3 | Re-entry workflow for post-green changes |
| `../../../../templates/artefact-impact-matrix.md` | 3 | Required `_changes/` worksheet for iterative changes |
| `../../../../methodology/implementation/STAGES.md` | 3 | Stage 04 routing contract |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rules |
| `../../../../reference-impl/java-micronaut-jena/CODE_STYLE.md` | 3 | Java profile conventions |
| `../../../../reference-impl/java-micronaut-jena/README.md` | 3 | Java runtime debug surface |

## Process

Run the sub-stages in order, gating after each:

1. [`04a_storage-mapping/`](04a_storage-mapping/CONTEXT.md) — not applicable (in-memory profile)
2. [`04b_spec/`](04b_spec/CONTEXT.md) — per-concept SPEC slice
3. [`04c_flow-tests/`](04c_flow-tests/CONTEXT.md) — outer red (flow tests)
4. [`04d_concept-tdd/`](04d_concept-tdd/CONTEXT.md) — router for `04d_red-tests/` then `04d_green-impl/`
5. [`04e_sync-tdd/`](04e_sync-tdd/CONTEXT.md) — router for `04e_red-tests/` then `04e_green-impl/`

During `04c` through `04e`, use the Java profile's debug endpoints as
the default runtime evidence surface for explaining live behaviour:
`/api/dev/flows` for registered sync order, `/api/dev/flow/{token}` for
one archived flow, `/api/dev/stuck` for active actions missing
`:output`, and `/api/dev/concept/{name}/triples` for concept-state
inspection. Do not treat predicted token chains alone as runtime proof.

For the `Web` bootstrap boundary, keep the controller transport-only:
normalize input, invoke the flow root, await the authored response, and
translate transport output. Do not call business concept classes
directly, branch on domain outcomes, compute domain policy, or
read/mutate concept state in the controller/route handler.

## Outputs

(none — see sub-stages)

## Verify

- Every sub-stage has been gated.
- For iterative changes, `quality-gate/verify_iterative_change_readiness.py`
	passes before 04d/04e work starts, and
	`quality-gate/verify_iterative_change_coupling.py` passes before merge.
- `04d_red-tests/` is approved before `04d_green-impl/` starts.
- `04e_red-tests/` is approved before `04e_green-impl/` starts.
- The flow tests from `04c` are green at the end of `04e_green`.
- Any runtime explanation of why a flow is red, green, stuck, or
	archived cites one of the Java profile debug endpoints or another
	executed runtime inspection command.
- Any `Web` implementation remains transport-only: no direct
  business-concept dependency, no domain branching, and no concept-state
  read/write in the controller/route handler.
- **Cross-stage check (back):** every concept in `02_concepts/output/` and every sync in `03_syncs/output/` has a corresponding sub-stage output.

## Gate

Default — fires only after `04e_green-impl/` is green.

## Next stage

-> [`04a_storage-mapping/CONTEXT.md`](04a_storage-mapping/CONTEXT.md) — Storage mapping

For in-memory profiles, skip 04a and go straight to [`04b_spec/CONTEXT.md`](04b_spec/CONTEXT.md). Mark 04a with a `_NOT_APPLICABLE.md` note in its `output/`.

The agent proceeds to the first applicable sub-stage without a human gate.
