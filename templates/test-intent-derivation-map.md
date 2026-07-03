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

> For Stage 04d.
>
> **London School TDD.** One test class per concept action. Class name:
> `<Concept><Action>Test` (e.g. `UserLookupByUsernameTest`). Use
> `@Nested` classes for preconditions (`WhenUserExists`,
> `WhenUserUnknown`). Method names use the
> `should<Behavior>When<Condition>` convention. Assertions verify
> interactions (outcome type, flow token presence), not internal state.
> Comment blocks use `// GIVEN` / `// WHEN` / `// THEN` instead of
> Arrange-Act-Assert. Use business terms from the concept spec and use
> case (ubiquitous language), not technical jargon.
>
> **Preconditions:** state that must exist before the action is called
> to make this outcome reachable. Write `none` if the outcome is
> reachable from a fresh instance. A test that cannot produce its
> expected outcome from a fresh instance without seeding prior state
> is a defect in the test, not the implementation.
>
> **Coverage rule:** every outcome defined in the SPEC slice
> (`04b_spec/output/`) must appear as at least one row, whether or not
> it is exercised by a flow test. Quote the spec line if the outcome
> does not appear in any flow test — this confirms it is spec-defined
> and not invented.

### `<Concept>.<action>` → test class: `<Concept><Action>Test`

| # | @Nested | Test method | Outcome | Source | Preconditions |
|---|---|---|---|---|---|
| 1 | `When<Precondition>` | `should<Behavior>When<Condition>()` | `<OUTCOME>` | Flow: `<scenario-name>` \| Spec: `<file>:<line>` | none \| `<description>` |

> Repeat this `###` block once per public action of each concept in scope.

## Sync rules → sync tests

> For Stage 04e. One test class per sync. Class name: `<SyncName>Test`
> (e.g. `WhenPasswordAuthCheckOkThenSessionGrantForLoginTest`). Use
> `@Nested` for trigger outcome groups (`WhenCheckOk`). Method names:
> `should<Trigger><Then>`.
> Assertions verify the downstream action was scheduled (interaction
> verification), not the downstream action's own behavior.

| Sync | @Nested class | Test method | Trigger pattern | Resulting actions |
|---|---|---|---|---|
| `<SyncName>` | `When<Trigger>` | `should<Trigger><Then>()` | `<Concept>.<action> -> <Outcome>` | `<list of expected then-actions>` |

## Notes

> Anything missing — actions or scenarios with no row — is a coverage
> gap that stage 05 verification will flag.

## Red-To-Green Handoff Bundle

> Required for Stages 04d and 04e before switching from red work to
> green work. This is the handoff packet for the implementor model.

| Item | Value |
|---|---|
| Approved test files | `<list>` |
| Exact package names | `<list>` |
| Exact class names | `<list>` |
| Exact method signatures under test | `<list>` |
| Red evidence command | `<command>` |
| Expected red outcome | `<failing tests / disabled stubs / etc.>` |
| Next implementation target | `<class/file>` |

> If this bundle is missing, the red stage is not ready to hand off to
> green implementation.
