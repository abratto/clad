# Stage 04e — Sync TDD (router)

## Pre-condition (agent must verify before starting)

Run the iterative-change readiness check before writing any artefacts:

```
python3 ../../../../../quality-gate/verify_iterative_change_readiness.py \
   --feature ../../../
```

If this reports an iterative concept/sync change with no valid `_changes/`
artefact, stop and complete the artefact-impact matrix first.

## Why this stage exists

This stage is the ICM router for sync TDD. It exists to make the London
School red/green handoff structural: `04e-red` derives and approves
sync tests, `04e-green` implements only against those approved tests and
turns the outer flow tests green.

**Feeds:**

- approved red sync tests + handoff bundle -> `04e_green-impl/`
- green sync implementation and green flow tests -> `05_verify/`

**Agent stance for this stage:**
- If a sync needs imperative branching to make a test pass, the defect
  is in Stage 03; push the branching down into concept outcomes and
  re-derive the sync.
- `04e-red` may write sync tests and derivation artefacts only.
- `04e-green` may implement only against approved `04e-red` tests.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../03_syncs/output/` | 4 | Sync specs |
| `../04b_spec/output/` | 4 | SPEC slices for the actions involved |
| `../04c_flow-tests/output/` | 4 | Outer flow expectations that must go green at the end |
| `../../../../../methodology/core/ITERATIVE_CHANGES.md` | 3 | Re-entry workflow for post-green sync changes |
| `../../../_config/build-and-test.md` | 3 | Canonical build/test command inherited by child stages |
| `../../../_config/package-and-layout.md` | 3 | Canonical package/source-root settings inherited by child stages |
| `../../../../../methodology/implementation/TDD.md` | 3 | London School structural handoff rules |

## Process

Run the child stages strictly in order, gating after each:

1. [`04e_red-tests/`](04e_red-tests/CONTEXT.md) — derive executable
   sync tests, run them red, and record the handoff bundle.
2. [`04e_green-impl/`](04e_green-impl/CONTEXT.md) — implement only
   against the approved red sync tests until they and the `04c` flow
   tests are green.

## Outputs

(none — child stages own outputs and side effects)

## Verify

- `04e_red-tests/` was gated before `04e_green-impl/` started.
- Iterative-change readiness passes before sync implementation work starts.
- `04e_red-tests/output/sync-test-derivation.md` exists.
- All approved sync tests are green at the end of `04e_green-impl/`.
- All flow tests from `04c` are green at the end of `04e_green-impl/`.
- No extra executable syncs exist without an approved Stage 03 sync.

## Gate

Auto-advances through Stage 05. Sync tests are mechanically derived
from approved chain tables and sync specs. The `verify_sync_matrix.py`
and `verify_scenario_coverage.py` scripts are the automated gates.
No human approval is required at the 04e-red boundary. The flow tests
from 04c must go green at the end of 04e-green.

## Next stage

-> [`04e_red-tests/CONTEXT.md`](04e_red-tests/CONTEXT.md) — Sync test derivation (red)

The agent proceeds without a human gate.
