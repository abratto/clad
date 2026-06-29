# Stage 04e-red — Sync Test Derivation (red)

## Pre-condition (agent must verify before starting)

Run the following **before** writing any sync test artefacts:

```
python3 ../../../../../../quality-gate/verify_stage_output.py \
  --feature ../../../../ \
  --required-stages 04d
```

Additionally, concept tests must be green (`mvn test` passes).
If either check fails, stop — concept implementation must be
complete before sync tests can be derived.

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
| Skill: `clad-sync-tdd` | 3 | Sync TDD reference (see skills/ directory) |
| `../../../../../../templates/test-intent-derivation-map.md` | 3 | Coverage template |
| `../../../../../../methodology/implementation/RULES.md` | 3 | Hard rule R3 |
| `../../../../../../methodology/implementation/TDD.md` | 3 | London School handoff semantics |
| `../../../../../../reference-impl/java-micronaut-jena/README.md` and `../../../../../../reference-impl/java-micronaut-jena/CODE_STYLE.md` (only when this profile is selected) | 3 | Profile conventions |
| `../../../../../../reference-impl/java-micronaut-jena/SYNC_LOWERING.md` (only when this profile is selected) | 3 | Deterministic Stage 03 -> SPARQL lowering contract |

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
- (Side effect:) `<SyncName>Test.java` (or profile equivalent) per sync

## Verify

### Automated checks

Run the following before requesting the human gate:

```
python3 ../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected "sync-test-derivation.md"
python3 ../../../../quality-gate/verify_test_naming.py \
  --test-source-root <APP_TEST_SOURCE_ROOT> \
  --scope syncs
```

- **verify_file_manifest.py:** `output/` contains exactly
  `sync-test-derivation.md`.
- **verify_test_naming.py:** every sync test class follows London School
  naming conventions (class: `<SyncName>Test`, method prefix: `should`,
  `@Nested` groups present, `// GIVEN/WHEN/THEN` comments).

### Semantic checks (human)

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

### Flow-test coverage

- Every Gherkin `Scenario` in `../../04c_flow-tests/output/*.feature` is
  covered by at least one sync test row in the derivation map.
- The sync test's trigger pattern matches the `When` step's expected
  token-chain root, and its expected actions match the chain-table rows
  that the step definitions will invoke.
- The Cucumber runner compiles (tests can stay red — the sync tests
  provide the behavioral failure evidence).

## Gate

Auto-advances to 04e-green. Sync tests are mechanically derived from
approved chain tables and sync specs. The `verify_sync_matrix.py` and
`verify_scenario_coverage.py` scripts must pass before advancing.

## Next stage

-> [`../04e_green-impl/CONTEXT.md`](../04e_green-impl/CONTEXT.md) — Implement approved sync tests only
