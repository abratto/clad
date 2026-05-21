# Stage 04e-red — Sync Test Derivation (red)

## Pre-condition (agent must verify before starting)

**`../../04d_concept-tdd/04d_green-impl/` must be complete and approved.**
If concept green work is not approved, stop and tell the human that
`04d-green` must finish before `04e-red` can begin.

## Why this stage exists

This is the **red half** of sync TDD. Its only job is to derive
executable sync tests from approved sync contracts and outer flow
expectations, run them red, and hand a precise contract to `04e-green`.
Making this a separate ICM folder gives weaker models a hard boundary:
no sync implementation belongs here.

**Feeds:**

- `output/sync-test-derivation.md` plus approved sync test files -> `04e-green`
- approved sync tests -> Stage 05 coverage trace

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../../03_syncs/output/` | 4 | Sync specs |
| `../../04b_spec/output/` | 4 | SPEC slices for participating actions |
| `../../04c_flow-tests/output/` | 4 | Outer expectations that must turn green |
| `../../04d_concept-tdd/04d_red-tests/output/` | 4 | Approved concept-level test derivation |
| `../../../../_config/build-and-test.md` | 3 | Canonical build/test command for red evidence |
| `../../../../_config/package-and-layout.md` | 3 | Canonical package/source-root settings |
| `../../../../../../templates/test-intent-derivation-map.md` | 3 | Coverage template |
| `../../../../../../methodology/implementation/RULES.md` | 3 | Hard rule R3 |
| `../../../../../../methodology/implementation/TDD.md` | 3 | London School handoff semantics |
| `../../../../../../reference-impl/java-micronaut-jena/README.md` and `../../../../../../reference-impl/java-micronaut-jena/CODE_STYLE.md` | 3 | Java profile conventions |

## Process

1. Derive sync tests from approved Stage 03 sync specs, the relevant
  SPEC slices, the outer expectations in `04c_flow-tests/output/`, and
  the expected authored action chain recorded there.
2. Write the sync test file(s) only under `APP_TEST_SOURCE_ROOT`.
   Do not write or modify sync implementation code in this stage.
3. Run the canonical command from `../../../../_config/build-and-test.md`
   and confirm the result is true red: test compilation succeeds and the
   sync tests fail for behavioral reasons.
4. Record the derivation map and the red-to-green handoff bundle in
   `output/sync-test-derivation.md`: approved test files, exact
   package/class/method names, red evidence command, expected red
   outcome, and the next implementation target.
5. Stop and present the red sync tests for human approval.

## Outputs

- `output/sync-test-derivation.md` — derivation map plus handoff bundle
- (Side effect:) `<SyncName>Test.java` per sync

## Verify

- `output/sync-test-derivation.md` exists.
- Every sync test row traces back to an approved Stage 03 sync plus the
  approved outer flow expectations it helps turn green. No sync test was
  invented without those sources.
- The handoff bundle names the expected authored action chain from `04c`
  that the green implementation must satisfy.
- Sync tests live under `APP_TEST_SOURCE_ROOT` and packages consistent
  with `APP_PACKAGE_ROOT`.
- Executed red evidence shows successful test compilation and
  behavioral test failure.
- No sync implementation was introduced or changed during this stage.
- The handoff bundle names the approved test files, exact
  package/class/method names, the red evidence command, expected red
  outcome, and the next implementation target.

## Gate

Default human approval. `04e-green` may not begin until this gate is
explicitly passed.

## Next stage

-> [`../04e_green-impl/CONTEXT.md`](../04e_green-impl/CONTEXT.md) — Implement approved sync tests only

To advance, the human says: **"Proceed to Stage 04e-green."**
