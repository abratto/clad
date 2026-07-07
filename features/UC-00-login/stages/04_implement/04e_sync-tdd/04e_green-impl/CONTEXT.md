# Stage 04e-green — Sync Implementation (green)

## Pre-condition (agent must verify before starting)

**`../04e_red-tests/output/sync-test-derivation.md` must exist and be
human-approved.** If the red sync tests are missing or not yet approved,
stop and send the work back to `04e-red`.

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
| `../../../../../../methodology/implementation/RULES.md` | 3 | Hard rule R3 |
| `../../../../../../methodology/implementation/TDD.md` | 3 | London School handoff semantics |
| `../../../../../../reference-impl/java-micronaut-jena/README.md` and `../../../../../../reference-impl/java-micronaut-jena/CODE_STYLE.md` | 3 | Java profile conventions |
| `../../../../../../reference-impl/java-micronaut-jena/CANONICAL_EXEMPLAR.md` | 3 | Java realization pattern, not source of truth |

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
   authored action chain, and the approved red sync tests. Use the Java
   canonical exemplar only as a realization pattern for class, package,
   SPARQL, and test shape.
5. Place sync code in the canonical Java sync package bucket: each
   approved sync becomes one class under `<APP_PACKAGE_ROOT>.syncs`,
   with tests mirrored under the corresponding sync test package. Do
   not place syncs in `engine`, `infrastructure`, `concepts`, or ad hoc
   sibling packages.
6. Keep sync logic declarative. Do not invent imperative coordinator
   classes, extra executable syncs, or branching business logic. A
   class that sequences ordered domain calls or chooses the final
   scenario branch inline is a defect, not an acceptable shortcut.
7. Run the canonical command from `../../../../_config/build-and-test.md`
   until sync tests are green and the `04c` flow tests are green, then
   stop for human approval.

## Outputs

- (Side effect:) `<SyncName>.java` and green `<SyncName>Test.java` files per sync

## Verify

- All approved sync tests are green.
- All flow tests from `04c` are green.
- Run `quality-gate/verify_iterative_change_coupling.py` before merge when
   sync implementation changed; matching Stage 03 sync artefacts must be in
   the same diff.
- Executed command evidence shows: test compilation succeeds, sync tests
  are green, and flow tests are green.
- Run `quality-gate/verify_implementation_parity.py` with the Java sync
   source directory and `--features-dir features/`. It must confirm every
   sync class has a corresponding Stage 03 spec and mechanically follows
   the `When<Trigger>Then<Target>[For<Scope>]` naming grammar.
- Run `quality-gate/verify_sync_implementation_parity.py` with
  `--sync-dir ../../../03_syncs/output/` and the Java sync source directory.
  It must confirm every approved Stage 03 sync contract has a corresponding
   `@Singleton` `SyncAgent` class.
- Behavior is traceable first to the approved upstream artefacts; the
   Java exemplar was used only as a realization pattern.
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
- Sync classes are under `<APP_PACKAGE_ROOT>.syncs` and not in `engine`,
   `infrastructure`, `api`, `concepts`, or ad hoc sibling packages.

## Gate

Default human approval. This is the gate before Stage 05.

## Next stage

-> [`../../../05_verify/CONTEXT.md`](../../../05_verify/CONTEXT.md) — Verify + close

To advance, the human says: **"Proceed to Stage 05."**
