# Stage 04d-red — Concept Test Derivation (red)

## Pre-condition (agent must verify before starting)

**`../../04c_flow-tests/output/` must be non-empty.** If it is empty,
stop immediately and tell the human that Stage 04c must be completed and
gated before `04d-red` can begin.

## Why this stage exists

This is the **red half** of concept TDD. Its only job is to derive
executable concept tests from approved outer artefacts, run them red,
and hand a precise contract to `04d-green`. Making this a separate ICM
folder gives weaker models a hard boundary: no production code belongs
here.

**Feeds:**

- `output/concept-test-derivation.md` plus approved test files -> `04d-green`
- approved concept tests -> Stage 05 coverage trace

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../../02_concepts/output/` | 4 | Concept specs |
| `../../04b_spec/output/` | 4 | SPEC slices to compile against |
| `../../04c_flow-tests/output/` | 4 | Drives test derivation |
| `../../../../_config/build-and-test.md` | 3 | Canonical build/test command for red evidence |
| `../../../../_config/package-and-layout.md` | 3 | Canonical package/source-root settings |
| `../../../../../../templates/test-intent-derivation-map.md` | 3 | Coverage template |
| `../../../../../../methodology/implementation/RULES.md` | 3 | Hard rules R1, R5, R14, R16 |
| `../../../../../../methodology/implementation/TDD.md` | 3 | London School derivation rules |
| `../../../../../../reference-impl/java-micronaut-jena/README.md` and `../../../../../../reference-impl/java-micronaut-jena/CODE_STYLE.md` | 3 | Java profile conventions |

## Process

1. Derive concept tests from approved outer artefacts. Start with
   `04c_flow-tests/output/`, then add any required action/outcome pairs
   from `04b_spec/output/` that are not exercised by the flow tests.
2. Write the concept test file(s) only under `APP_TEST_SOURCE_ROOT`.
   Do not write or modify production implementation code in this stage.
3. After asserting each outcome token, assert the primary completion
  fields that `writeCompletion` writes and downstream syncs consume.
  Outcome-only tests are incomplete.
4. Run the canonical command from `../../../../_config/build-and-test.md`
   and confirm the result is true red: test compilation succeeds and the
   tests fail for behavioral reasons.
5. Record the derivation map and the red-to-green handoff bundle in
   `output/concept-test-derivation.md`: approved test files, exact
   package/class/method names, red evidence command, expected red
   outcome, and the next implementation target.
6. Stop and present the red tests for human approval.

## Outputs

- `output/concept-test-derivation.md` — derivation map plus handoff bundle
- (Side effect:) `<Name>ConceptTest.java` per concept

## Verify

- `output/concept-test-derivation.md` exists.
- Every test row traces back to an approved `04c` flow test or an
  approved `04b` SPEC outcome. No test case was invented without one of
  those sources.
- Run `quality-gate/verify_concept_field_assertions.py` with the UC-00
  SPEC directory and Java test source root; every concept test that
  asserts an outcome must also assert required completion fields.
- Every concept test asserts the outcome and the primary completion
  fields downstream syncs consume; no valid-input primary field assertion
  accepts null or empty string.
- Tests live under `APP_TEST_SOURCE_ROOT` and packages consistent with
  `APP_PACKAGE_ROOT`.
- Executed red evidence shows successful test compilation and
  behavioral test failure.
- No test depends on another concept's state or sync orchestration;
  those cases belong in `04e`.
- No production concept implementation was introduced or changed during
  this stage.
- The handoff bundle names the approved test files, exact
  package/class/method names, the red evidence command, expected red
  outcome, and the next implementation target.

## Gate

Default human approval. `04d-green` may not begin until this gate is
explicitly passed.

## Next stage

-> [`../04d_green-impl/CONTEXT.md`](../04d_green-impl/CONTEXT.md) — Implement approved concept tests only

To advance, the human says: **"Proceed to Stage 04d-green."**
