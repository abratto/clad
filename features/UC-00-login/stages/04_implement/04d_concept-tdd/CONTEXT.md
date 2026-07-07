# Stage 04d — Concept TDD (router)

## Pre-condition (agent must verify before starting)

**`../04c_flow-tests/output/` must be non-empty.** If it is empty, stop
immediately and tell the human that Stage 04c must be completed and
gated before Stage 04d can begin.

Run the iterative-change readiness check before writing any artefacts:

```
python3 ../../../../../quality-gate/verify_iterative_change_readiness.py \
   --feature ../../../
```

If this reports an iterative concept/sync change with no valid `_changes/`
artefact, stop and complete the artefact-impact matrix first.

## Why this stage exists

This stage is the ICM router for concept TDD. It exists to make the
London School red/green handoff structural: `04d-red` derives and
approves tests, `04d-green` implements only against those approved
tests.

**Feeds:**

- approved red concept tests + handoff bundle -> `04d_green-impl/`
- green concept implementation -> `04e_sync-tdd/`

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../02_concepts/output/` | 4 | Concept specs |
| `../04b_spec/output/` | 4 | SPEC slices to compile against |
| `../04c_flow-tests/output/` | 4 | Pre-condition check + drives child-stage work |
| `../../../../../methodology/core/ITERATIVE_CHANGES.md` | 3 | Re-entry workflow for post-green concept changes |
| `../../../_config/build-and-test.md` | 3 | Canonical build/test command inherited by child stages |
| `../../../_config/package-and-layout.md` | 3 | Canonical package/source-root settings inherited by child stages |
| `../../../../../methodology/implementation/TDD.md` | 3 | London School structural handoff rules |

## Process

Run the child stages strictly in order, gating after each:

1. [`04d_red-tests/`](04d_red-tests/CONTEXT.md) — derive executable
   concept tests, run them red, and record the handoff bundle.
2. [`04d_green-impl/`](04d_green-impl/CONTEXT.md) — implement only
   against the approved red tests until they are green.

## Outputs

(none — child stages own outputs and side effects)

## Verify

- `04d_red-tests/` was gated before `04d_green-impl/` started.
- Iterative-change readiness passes before concept implementation work starts.
- `04d_red-tests/output/concept-test-derivation.md` exists.
- All approved concept tests are green at the end of `04d_green-impl/`.
- No cross-concept imports.
- Every public concept action emits a flow token.
- **Boundary rule:** any test or implementation path that depends on
  another concept's state or a sync belongs in `04e`, not `04d`.

## Gate

Auto-advances (next human gate: Stage 04c already passed). The gate fires
only after `04d_green-impl/` is green.

## Next stage

-> [`04d_red-tests/CONTEXT.md`](04d_red-tests/CONTEXT.md) — Concept test derivation (red)

To advance, the human says: **"Proceed to Stage 04d-red."**
