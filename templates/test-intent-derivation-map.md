<!-- Template for Stages 04c / 04d / 04e. Purpose: see methodology/implementation/STAGES.md §"Stage 04c–e". -->

# Test-intent derivation map — `<scope>`

> Shows which test exercises which contract element. The human reads
> this at a glance to verify coverage; missing rows surface as
> verification findings in stage 05.

## Use-case scenarios → flow tests

> For Stage 04c. One row per named scenario in the use case.

| Scenario | Trigger | Flow test | Status |
|---|---|---|---|
| `<scenario-name>` | `<HTTP/event>` | `<TestClass>.<testMethod>` | red \| green |

## Concept actions → concept tests

> For Stage 04d. One row per public action of each concept in scope.
> **Preconditions:** state that must exist before the action is called
> to make this outcome reachable. Write `none` if the outcome is
> reachable from a fresh instance. A test that cannot produce its
> expected outcome from a fresh instance without seeding prior state
> is a defect in the test, not the implementation.

| Concept | Action | Preconditions | Outcome under test | Test | Status |
|---|---|---|---|---|---|
| `<Concept>` | `<action>` | `none` \| `<description of required prior state>` | `<Outcome>` | `<TestClass>.<testMethod>` | red \| green |

## Sync rules → sync tests

> For Stage 04e. One row per sync rule.

| Sync | Trigger pattern | Resulting actions checked | Test | Status |
|---|---|---|---|---|
| `<SyncName>` | `<Concept>.<action> -> <Outcome>` | `<list of expected then-actions>` | `<TestClass>.<testMethod>` | red \| green |

## Notes

> Anything missing — actions or scenarios with no row — is a coverage
> gap that stage 05 verification will flag.
