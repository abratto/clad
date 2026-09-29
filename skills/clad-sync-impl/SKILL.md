---
name: clad-sync-impl
description: Implement declarative syncs and their unit tests during CLAD Stage 04e. Use when deriving sync tests from approved sync specs and the 04c Acceptance Spec, then producing the declarative sync implementation alongside them in a single stage. Test effectiveness is gated by mutation score.
---

# CLAD Sync Implementation (Stage 04e)

> **Role:** required stage guidance for Stage 04e. The stage `CONTEXT.md`
> `Inputs` table is authoritative for *which files to load*; load those
> exactly. Follow the canonical `java-legible` profile's conventions.

## What this skill covers

Stage 04e is a **single stage**: the sync unit tests and the declarative
sync implementation are produced together. There is no red/green
sub-stage split and no handoff bundle. The tests derive from the approved
Stage 03 sync specs; they assert that the correct downstream action is
*scheduled* for a given trigger outcome. This is where the 04c
Acceptance Spec tests finally go green.

## Files

The stage `CONTEXT.md` `Inputs` names the loading set: `03` sync specs,
`03a` dependency-review cards, `04b` contracts, the `04c` Acceptance Spec,
`04d` verification evidence, `_config/build-and-test.md`,
`_config/package-and-layout.md`, `TESTING.md`, `RULES.md`,
`templates/test-intent-derivation-map.md`, `templates/sync-summary.md`.
Profile reference docs are loaded only when that profile is selected.

## Process

1. **Derive `output/sync-test-derivation.md`** from the approved Stage 03
   sync specs using the derivation-map template: one row per sync,
   trigger pattern → the exact then-actions it must schedule.
2. **Write the sync unit tests** under `APP_TEST_SOURCE_ROOT`. Assert the
   downstream action was scheduled; do not assert its own behaviour.
3. **Implement each sync** as a declarative rule so the tests pass. A
   sync is `when … where … then …` — no imperative coordinator or
   branching (R3). Every action writes an `outcome` field (R12).
   Shared-trigger syncs declare route scope (R11/R15).
4. **Write `output/verification-evidence.md`** recording the executed
   build-and-test command and result, the now-green acceptance tests, and
   the mutation score when `mutation.command` is configured.
5. Run the canonical build-and-test command from
   `_config/build-and-test.md`; the 04c acceptance tests must all pass.

Self-audit: run `python3 quality-gate/verify_artefacts.py` before advancing.

## Hard constraints

- Tests and implementation are produced together — implement nothing
  before its unit test exists (R8).
- No imperative coordinator/orchestrator classes.
- Implement exactly the approved Stage 03 sync set — no extras.
- The 04c acceptance tests must go green by the end of this stage.
- Sync logic is declarative (R3).
- Shared-trigger syncs declare route scope (R11/R15).
- Test effectiveness is the mutation score (`mutation.command` /
  `mutation.threshold`, checked by `verify_mutation_score.py`) — not a
  red-green ritual or a test count.

## Test naming (advisory)

CLAD recommends, but does not gate, these interaction-focused conventions
for sync unit tests (`verify_test_naming.py` reports drift, it does not
block):

- **Class name:** `<SyncName>Test` (e.g.
   `GrantForLoginWhenCheckOkTest`)
- **`@Nested` class:** `When<Trigger>` groups by the trigger outcome
  (e.g. `WhenCheckOk`, `WhenCheckBadPassword`)
- **Method name:** `should<Trigger><Then>` verifies interactions
  (e.g. `shouldFireSessionGrant`, `shouldNotFire`)
- **Assertions:** verify the downstream action was scheduled (SPARQL
  CONSTRUCT or engine state), not the downstream action's own behavior
- **Comment blocks:** `// GIVEN` / `// WHEN` / `// THEN`

```java
class GrantForLoginWhenCheckOkTest {
    @Nested class WhenCheckOk {
        @Test void shouldFireSessionGrant() {
            // GIVEN: a PasswordAuth.check action completed with outcome OK
            // WHEN: the sync dispatcher runs
            // THEN: a Session.grant invocation is scheduled
        }
    }
}
```
