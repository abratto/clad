---
name: clad-sync-tdd
description: Execute sync-level TDD during CLAD Stage 04e. Use when deriving red sync tests from approved sync specs, then implementing green sync classes that turn both sync tests and outer flow tests green. Completes the London School double-loop.
---

# CLAD Sync TDD (Stage 04e)

> **Role:** required stage guidance for Stage 04e. The stage `CONTEXT.md`
> `Inputs` table is authoritative for *which files to load*; load those
> exactly. Profile conventions are **conditional**: follow the canonical
> `java-legible` profile unless `clad.properties` selects a legacy
> (`java-micronaut-jena`) profile.

## What this skill covers

The inner (sync) loop of London School TDD: `04e-red` derives executable
sync tests from approved sync contracts and outer flow expectations, and
`04e-green` implements only against those approved tests until both sync
tests and the outer flow tests from `04c` are green.

## Files

The stage `CONTEXT.md` `Inputs` names the loading set: `03` sync specs,
`04b` SPECs, `04c` flow tests, `_config/build-and-test.md`,
`_config/package-and-layout.md`, `TDD.md`, `RULES.md`,
`templates/sync-summary.md`, `templates/test-intent-derivation-map.md`.
Profile reference docs are loaded only when that profile is selected.

## Process

1. **04e-red**: Derive sync tests from approved Stage 03 sync specs
   and `04c` outer flow expectations. Write test files under
   `APP_TEST_SOURCE_ROOT`. Run red. Record the handoff bundle.
2. **04e-green**: Read approved red sync tests. Extract exact
   signatures. Implement sync classes. Keep logic declarative — no
   imperative coordinator classes. Run until sync tests are green AND
   the outer flow tests from `04c` are green.

Self-audit: run `python3 quality-gate/verify_artefacts.py` before advancing.

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
