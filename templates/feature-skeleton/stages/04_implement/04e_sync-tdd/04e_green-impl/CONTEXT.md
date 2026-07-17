# Stage 04e-green — Sync Implementation (green)

## Pre-condition (agent must verify before starting)

Run the following **before** writing any sync implementation code:

```
python3 ../../../../../../quality-gate/verify_stage_output.py \
  --feature ../../../../ \
  --required-stages 04e
```

If this script exits with a non-zero status, stop immediately.
Stage 04e-red sync test derivation is missing — do not implement
before sync tests are derived.

## Why this stage exists

This is the **green half** of sync TDD. Its only job is to implement
exactly what the approved red sync tests require and turn the outer flow
tests green. Making this a separate ICM folder gives weaker models a
hard boundary: implementation may consult earlier artefacts, but it may
not redesign approved tests.

**Feeds:**

- green sync implementation -> Stage 05
- green flow tests from `04c` -> Stage 05

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../../03_syncs/output/` | 4 | Sync specs |
| `../../04b_spec/output/` | 4 | SPEC slices for participating actions |
| `../../04c_flow-tests/output/` | 4 | Outer flow tests that must now go green |
| `../04e_red-tests/output/` | 4 | Approved red sync tests and handoff bundle |
| `../../../../_config/build-and-test.md` | 3 | Canonical build/test command for green evidence |
| `../../../../_config/package-and-layout.md` | 3 | Canonical package/source-root settings |
| Skill: `clad-sync-tdd` | 3 | Sync TDD reference (see skills/ directory) |
| `../../../../../../methodology/implementation/RULES.md` | 3 | Hard rule R3 |
| `../../../../../../methodology/implementation/TDD.md` | 3 | London School handoff semantics |
| `../../../../../../reference-impl/java-micronaut-jena/README.md` and `../../../../../../reference-impl/java-micronaut-jena/CODE_STYLE.md` (only when this profile is selected) | 3 | Profile conventions |
| `../../../../../../reference-impl/java-micronaut-jena/SYNC_LOWERING.md` (only when this profile is selected) | 3 | Deterministic Stage 03 -> SPARQL lowering contract |
| `../../../../../../reference-impl/java-micronaut-jena/CANONICAL_EXEMPLAR.md` (only when this profile is selected) | 3 | Profile realization pattern, not source of truth |

## Process

1. Read the approved red sync tests and the handoff bundle from
   `../04e_red-tests/output/`.
2. Extract and match exactly: package declarations, class names, method
   signatures, referenced helper symbols, and test expectations.
3. Implement only what is needed to make the approved sync tests pass.
   Do not redesign the tests during this stage. If they appear wrong,
   stop and send the work back to `04e-red` or Stage 03.
4. Derive behavior from the approved upstream artefacts first: the
   Stage 03 sync specs, the `04b` SPEC slices, the `04c` expected
   authored action chain, and the approved red sync tests. If the
   selected profile is Java/Jena/Micronaut, use
   `SYNC_LOWERING.md` as the deterministic lowering contract and
   `CANONICAL_EXEMPLAR.md` only as a realization pattern for class,
   package, and test shape. Neither may override the feature's own
   approved artefacts.
5. If the selected profile is Java/Jena/Micronaut, place sync code in
   the canonical sync package bucket: each approved sync becomes one
   class under `<APP_PACKAGE_ROOT>.syncs`, with tests mirrored under the
   corresponding sync test package. Do not place syncs in `engine`,
   `infrastructure`, `concepts`, or ad hoc sibling packages.
6. Keep sync logic declarative. Do not invent imperative coordinator
   classes, extra executable syncs, or branching business logic. A
   class that sequences ordered domain calls or chooses the final
   scenario branch inline is a defect, not an acceptable shortcut.
 7. Run the canonical command from `../../../../_config/build-and-test.md`
    until sync tests are green and the `04c` flow tests are green, then
    stop for human approval.
 8. On the Gherkin track: after sync tests and flow tests are green,
    enable the Cucumber runner (remove `@Disabled` from step-definition
    classes) and re-run. Confirm all Gherkin scenarios pass. Capture
    the Cucumber report (HTML or JSON) as supplementary gate evidence.

## Outputs

- (Side effect:) `<SyncName>.java` and green `<SyncName>Test.java` files (or profile equivalents) per sync

## Verify

- All approved sync tests are green.
- All flow tests from `04c` are green.
- Run `quality-gate/verify_iterative_change_coupling.py` before merge when
   sync implementation changed; matching Stage 03 sync artefacts must be in
   the same diff.
- Executed command evidence shows: test compilation succeeds, sync tests
  are green, and flow tests are green.
- Run `quality-gate/verify_implementation_parity.py` with
   `--sync-impl-dir <APP_SOURCE_ROOT>/<APP_PACKAGE_ROOT>/syncs` and
   `--features-dir ../../../../../../features`. It must confirm every sync class
   has a corresponding Stage 03 spec and mechanically follows the
   `When<Trigger>Then<Target>[For<Scope>]` naming grammar.

### Cucumber-green gate

```
python3 ../../../../../../quality-gate/verify_cucumber_green.py \
  --feature-root ../../../../ \
  [--test-command <your-build-and-test-command>]
```

- **verify_cucumber_green.py:** runs the test command and confirms all
  Cucumber scenarios pass. Fails on undefined/skipped/failing
  scenarios. Passes only when every Gherkin scenario is green.

### Flow-test verification

- All Gherkin scenarios in `../../04c_flow-tests/output/*.feature` are
  green via the Cucumber runner.
- The Cucumber report (HTML or JSON) is captured alongside the executed
  build-and-test evidence and shows 0 failed scenarios.
- The runtime token chain observed by each passing Gherkin scenario
  matches the expected authored action chain recorded in
  `../../04c_flow-tests/output/` for each scenario.
- Behavior is traceable first to the approved upstream artefacts; any
   profile exemplar was used only as a realization pattern.
- Every generated sync test/implementation pair corresponds to exactly
  one approved Stage 03 sync; no extra executable syncs exist without an
  upstream sync contract.
- No coordinator / orchestrator class was introduced to sequence domain
   calls imperatively unless an explicit methodology waiver exists.
- Green was reached through declared concept outcomes and sync triggers,
   not by inline business branching in implementation code.
- The resulting runtime/action shape matches the expected authored
   action chain recorded in `04c_flow-tests/output/` for each scenario.
- Green implementation treated the approved sync tests as the immediate
  contract and did not redesign them against earlier prose artefacts.
- Sync implementation package/source path matches
  `../../../../_config/package-and-layout.md` (`APP_PACKAGE_ROOT`,
  `APP_SOURCE_ROOT`, `APP_TEST_SOURCE_ROOT`).
- For the Java/Jena/Micronaut profile, sync classes are under
   `<APP_PACKAGE_ROOT>.syncs` and not in `engine`, `infrastructure`,
   `api`, `concepts`, or ad hoc sibling packages.

## Gate

Auto-advances to Stage 05. All sync tests and the 04c flow tests
must be green (`mvn test` passes) before advancing.

## Next stage

-> [`../../../05_verify/CONTEXT.md`](../../../05_verify/CONTEXT.md) — Verify + close

The agent proceeds to Stage 05 without a human gate.
