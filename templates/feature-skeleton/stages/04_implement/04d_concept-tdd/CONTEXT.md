# Stage 04d — Concept TDD (router)

## Pre-condition (agent must verify before starting)

Run the following **before** writing any artefacts for this stage:

```
python3 ../../../../../quality-gate/verify_gate_approval.py \
  --feature ../../../ \
  --required-gates 3
```

If this script exits with a non-zero status, stop immediately.
Gate 3 has not been approved — do not proceed.

**Additionally:** `../04c_flow-tests/output/` must be non-empty.
If it is empty, stop and tell the human that Stage 04c flow tests
have not been produced.

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
| `../../02_concepts/output/` | 4 | Concept specs |
| `../04b_spec/output/` | 4 | SPEC slices to compile against |
| `../04c_flow-tests/output/` | 4 | Pre-condition check + drives child-stage work |
| `../../../../../methodology/core/ITERATIVE_CHANGES.md` | 3 | Re-entry workflow for post-green concept changes |
| `../../../_config/build-and-test.md` | 3 | Canonical build/test command inherited by child stages |
| `../../../_config/package-and-layout.md` | 3 | Canonical package/source-root settings inherited by child stages |
| `../../../../../methodology/implementation/TDD.md` | 3 | London School structural handoff rules |
| `../../../../../../reference-impl/java-micronaut-jena/SYNC_LOWERING.md` (only when this profile is selected) | 3 | Concept SPARQL patterns (SELECT, UPDATE, writeCompletion, test fixtures) |

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

Auto-advances through Stage 05. Concept tests are mechanically derived
from the approved use case (04c) and SPECs (04b). The red→green handoff
is automated — `verify_concept_test_derivation.py` is the gate between
04d-red and 04d-green. No human approval is required at this boundary;
the design was settled at 04c (Gate 3).

## Next stage

-> [`04d_red-tests/CONTEXT.md`](04d_red-tests/CONTEXT.md) — Concept test derivation (red)

The agent proceeds without a human gate.
