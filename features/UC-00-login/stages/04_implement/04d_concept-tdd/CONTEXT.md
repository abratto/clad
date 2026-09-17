<!--
  WORKED EXAMPLE - contract synced from templates/feature-skeleton/.
  UC-00's output/ is historical/frozen (gate content hashes); it may
  contain legacy artefacts. See features/UC-00-login/README.md
  SS"Contract vs example".
-->

# Stage 04d — Concept TDD (router)

## Pre-condition

`advance.py` enforces stage order and upstream gate approval before this
stage runs — see `STAGES.md` §"Stage lifecycle (standard)". Do not start
until it has printed this stage as `NEXT STAGE`.

## Why this stage exists

This stage is the ICM router for concept TDD. It exists to make the
London School red/green handoff structural: `04d-red` derives and
approves tests, `04d-green` implements only against those approved
tests. One concept, one test fixture, no other concepts in scope (R1).

**Feeds:**

- approved red concept tests + handoff bundle -> `04d_green-impl/`
- green concept implementation -> `04e_sync-tdd/`

**Agent stance for this stage:**
- Read `methodology/implementation/TDD.md` before starting either child stage.
- If a test needs another concept's state or sync orchestration, it does not belong in `04d`; send it to `04e`.
- `04d-red` may write tests and derivation artefacts only.
- `04d-green` may implement only against approved `04d-red` tests.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../02_concepts/output/concept-bindings.md` | 4 | Which canonical concepts this feature uses |
| `../../../../../features/_system/concepts/` | 4 | Canonical concept specs (`state`, actions) |
| `../../02_concepts/output/<Name>.concept.md` | 4 | NEW/EXTEND proposals (not yet promoted) |
| `../04b_contract/output/` | 4 | Contract slices to compile against |
| `../04c_flow-tests/output/` | 4 | Pre-condition check + drives child-stage work |
| `../../../../../methodology/core/ITERATIVE_CHANGES.md` | 3 | Re-entry workflow for post-green concept changes |
| `../../../_config/build-and-test.md` | 3 | Canonical build/test command inherited by child stages |
| `../../../_config/package-and-layout.md` | 3 | Canonical package/source-root settings inherited by child stages |
| `../../../../../methodology/implementation/TDD.md` | 3 | London School structural handoff rules |
| `../../../../../reference-impl/legible-engine/README.md` (default profile) | 3 | Canonical engine contract (`Concept`, `SyncRule`, `Region`) |

## Process

The child stages are executable auto-advance stages. Run them strictly in order:

1. [`04d_red-tests/`](04d_red-tests/CONTEXT.md) — derive executable
   concept tests, run them red, and record the handoff bundle.
2. [`04d_green-impl/`](04d_green-impl/CONTEXT.md) — implement only
  against the completed red tests until they are green.


## Progress checklist

- [ ] Red tests derived from contract outcomes
- [ ] Every contract outcome has a matching test method
- [ ] Tests assert field values, not just outcomes (R14/R16)
- [ ] Green implementation makes all concept tests pass
- [ ] Self-audit: `./clad verify` passes
## Outputs

(none — child stages own outputs and side effects)

## Verify

- `04d_red-tests/` was complete before `04d_green-impl/` started.
- Iterative-change readiness passes before concept implementation work starts.
- `04d_red-tests/output/concept-test-derivation.md` exists.
- All approved concept tests are green at the end of `04d_green-impl/`.
- No cross-concept imports.
- Every public concept action emits a flow token.
- **Boundary rule:** any test or implementation path that depends on
  another concept's state or a sync belongs in `04e`, not `04d`.

## Gate

Auto-advances through `04d-red`, `04d-green`, then `04e-red`. Concept tests are mechanically derived
from the approved use case (04c) and contracts (04b). The red→green handoff
is automated — `verify_concept_test_derivation.py` is the gate between
04d-red and 04d-green. No human approval is required at this boundary;
the design was settled at 04c (Gate 3).

## Next stage

-> [`04d_red-tests/CONTEXT.md`](04d_red-tests/CONTEXT.md) — Concept test derivation (red)

The agent proceeds without a human gate.
