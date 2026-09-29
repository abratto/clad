<!-- Template for Stages 04d / 04e. Purpose: see methodology/implementation/TESTING.md. -->

# Test-intent derivation map — `<scope>`

> Shows which test exercises which contract element. The human reads
> this at a glance to verify coverage; missing rows surface as
> verification findings in stage 05. Tests are derived from already-approved
> artefacts and produced alongside the implementation — there is no red/green
> sub-stage split (DR-0001).

## Concept actions → concept tests

> For Stage 04d.
>
> One test class per concept action. Class name: `<Concept><Action>Test`
> (e.g. `UserLookupByUsernameTest`). Use `@Nested` classes for
> preconditions (`WhenUserExists`, `WhenUserUnknown`). Method names use the
> `should<Behavior>When<Condition>` convention. Assertions verify the
> `outcome` and the primary completion field values downstream syncs read
> (R14/R16) — not internal state.
>
> **Preconditions:** state that must exist before the action is called
> to make this outcome reachable. Write `none` if the outcome is
> reachable from a fresh instance. A test that cannot produce its
> expected outcome from a fresh instance without seeding prior state
> is a defect in the test, not the implementation.
>
> **Coverage rule:** every outcome defined in the contract slice
> (`04b_contract/output/`) must appear as at least one row, whether or not
> it is exercised by an acceptance test. Quote the spec line if the outcome
> does not appear in any acceptance scenario — this confirms it is
> spec-defined and not invented.

### `<Concept>.<action>` → test class: `<Concept><Action>Test`

| # | @Nested | Test method | Outcome | Source | Preconditions |
|---|---|---|---|---|---|
| 1 | `When<Precondition>` | `should<Behavior>When<Condition>()` | `<OUTCOME>` | Acceptance: `<scenario-name>` \| Spec: `<file>:<line>` | none \| `<description>` |

> Repeat this `###` block once per public action of each concept in scope.

## Sync rules → sync tests

> For Stage 04e. One test class per sync. Class name: `<SyncName>Test`
> (e.g. `GrantForLoginWhenCheckOkTest`). Use
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
