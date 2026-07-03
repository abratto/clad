---
name: clad-sync-tdd
description: Execute sync-level TDD during CLAD Stage 04e. Use when deriving red sync tests from approved sync specs, then implementing green sync classes that turn both sync tests and outer flow tests green. Completes the London School double-loop.
---

# CLAD Sync TDD (Stage 04e)

## What this skill covers

The inner (sync) loop of London School TDD: `04e-red` derives executable
sync tests from approved sync contracts and outer flow expectations, and
`04e-green` implements only against those approved tests until both sync
tests and the outer flow tests from `04c` are green.

## Quick reference

Load these files:

1. `methodology/implementation/TDD.md` — London School handoff semantics,
   outer-loop timing
2. `methodology/implementation/RULES.md` — hard rule R3
3. `templates/sync-summary.md` — sync test patterns
4. `templates/test-intent-derivation-map.md` — coverage template
5. `features/UC-XX-<slug>/stages/03_syncs/output/` —
   approved sync specs
6. `features/UC-XX-<slug>/stages/04b_spec/output/` —
   SPEC slices
7. `features/UC-XX-<slug>/stages/04c_flow-tests/output/` —
   outer flow tests that must go green
8. `features/UC-XX-<slug>/_config/build-and-test.md` —
   canonical test command
9. `features/UC-XX-<slug>/_config/package-and-layout.md` —
   canonical package/source-root settings
10. `reference-impl/java-micronaut-jena/README.md`,
     `reference-impl/java-micronaut-jena/CODE_STYLE.md`,
     `reference-impl/java-micronaut-jena/SYNC_LOWERING.md`, and
     `reference-impl/java-micronaut-jena/CANONICAL_EXEMPLAR.md` — profile
     conventions (only when this profile is selected)
11. The current stage `CONTEXT.md` for exact Inputs/Outputs/Process

## Process

1. **04e-red**: Derive sync tests from approved Stage 03 sync specs
   and `04c` outer flow expectations. Write test files under
   `APP_TEST_SOURCE_ROOT`. Run red. Record the handoff bundle.
2. **04e-green**: Read approved red sync tests. Extract exact
   signatures. Implement sync classes. Keep logic declarative — no
   imperative coordinator classes. Run until sync tests are green AND
   the outer flow tests from `04c` are green.

## Hard constraints

- **Red phase**: sync tests only — no implementation code.
- **Green phase**: implementation only — do not rewrite approved tests.
- No imperative coordinator/orchestrator classes.
- Implement exactly the approved Stage 03 sync set — no extras.
- Outer flow tests must go green at the end of `04e-green`.
- Sync logic is declarative (R3).

## Test naming (London School BDD)

Follow the London School interaction-focused convention for sync unit tests:

- **Class name:** `<SyncName>Test` (e.g.
   `WhenPasswordAuthCheckOkThenSessionGrantForLoginTest`)
- **`@Nested` class:** `When<Trigger>` groups by the trigger outcome
  (e.g. `WhenCheckOk`, `WhenCheckBadPassword`)
- **Method name:** `should<Trigger><Then>` verifies interactions
  (e.g. `shouldFireSessionGrant`, `shouldNotFire`)
- **Assertions:** verify the downstream action was scheduled (SPARQL
  CONSTRUCT or engine state), not the downstream action's own behavior
- **Comment blocks:** `// GIVEN` / `// WHEN` / `// THEN`

```java
class WhenPasswordAuthCheckOkThenSessionGrantForLoginTest {
    @Nested class WhenCheckOk {
        @Test void shouldFireSessionGrant() {
            // GIVEN: a PasswordAuth.check action completed with outcome OK
            // WHEN: the sync dispatcher runs
            // THEN: a Session.grant invocation is scheduled
        }
    }
}
```
