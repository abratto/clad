<!-- Maintenance-route planning record. -->
# Maintenance change — `legible-engine-trigger-index`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `legible-engine` (shared by `java-legible`, `legible-storage`, and all `dev.legible.engine`-based profiles)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Replace the drain loop's linear scan of `SyncRule` instances with a `concept/action/outcome` trigger index built once at engine construction.

## Why

`SyncEngine.processInvocation` matched syncs by looping over the full
`List<SyncRule>` and calling `SyncRule.matches(...)` (a three-value string
comparison) on every completion. This is O(total rules) per completion. For
features with hundreds of syncs (the engine's documented scaling horizon), the
scan becomes avoidable overhead, and the `matches` method encoded matching logic
inside the data type rather than in the engine, which is the one place matching
should live. The change introduces a `Map<String, List<SyncRule>>` index keyed
`concept/action/outcome` (with outcome-agnostic rules filed under bare
`concept/action`), so the drain loop fetches only the rules whose trigger
actually matches — O(matching rules) per completion. Matching semantics, firing
order, and exactly-once dedup are unchanged.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | No concept/sync signatures change; only the engine's internal match lookup changes. |
| Action ordering and sync deduplication | preserved | Buckets preserve declaration order; `hasEmission` exactly-once dedup untouched. |
| Flow-token lineage | preserved | `parentActionId`/`causedBySync` provenance paths unchanged — only the rule enumeration source changes. |
| Storage/retention semantics | preserved | No `FactStore`/`Region`/archiver change. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | no | `ENGINE.md` behavior unchanged; no spec edit required. |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | yes | `legible-engine/src/main/java/dev/legible/engine/SyncEngine.java` (index field + `buildTriggerIndex`/`matchingRules`/`key` helpers; drain loop uses `matchingRules`), `SyncRule.java` (remove unused `matches` method). |
| Profile tests | yes | New `legible-engine/src/test/java/dev/legible/engine/SyncTriggerIndexTest.java` (3 tests: shared bucket ordering, outcome-agnostic coexistence, cross-concept isolation). Existing suites re-run to confirm no regression. |
| UC artefact chain | no | No concept/sync spec or spec-parity surface changes; the `.sync.md` → `SyncRule` lowering is unchanged. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Shared-trigger bucket fires all rules in declaration order | unit | `SyncTriggerIndexTest.sharedTriggerFiresEveryMatchingRuleInDeclarationOrder` | pass | `mvn -q test -pl legible-engine` |
| Outcome-agnostic (`null`) rules coexist with exact rules | unit | `SyncTriggerIndexTest.outcomeAgnosticRuleFiresForAnyOutcomeAlongsideExactRules` | pass | `mvn -q test -pl legible-engine` |
| Rules keyed to other concepts/outcomes do not fire | unit | `SyncTriggerIndexTest.manyRulesDoNotCollideAcrossConceptsOrOutcomes` | pass | `mvn -q test -pl legible-engine` |
| Full legacy + rich-profile regression (login/social/tagging/token, fire-after-commit, replay) | unit + flow | `mvn -q test -pl legible-engine,java-legible,clad-engine` | pass | 40 `java-legible` + 16 `legible-engine` + `clad-engine` green |

## Gates

### Design gate

The human reviews contract impact, non-goals, and the test matrix before a
maintenance-scoped implementation or deployment file changes. Approve with
`./clad approve-maintenance legible-engine-trigger-index design`, then set Status to `active`.

### Evidence gate

The human reviews the completed test matrix and runtime evidence before commit.
After approval, set Status to `closed` and commit the record with the change.

## Notes

- **Purely internal + additive.** The public `SyncEngine` constructor signatures
  and `SyncRule` data shape are unchanged; only `SyncRule.matches` (a public
  convenience method, not on any profile's contract surface) is deleted. No
  downstream profile code calls it (verified via grep across `reference-impl/`).
- **Not intended to change observable scaling limits**, only to remove an
  avoidable O(n) scan; the engine's real scaling constraints (per-flow log
  sharding, per-concept locking, storage) are out of scope here.
- This record covers the trigger-index change only. The two-dimensional
  workflow-control change has its own record
  (`maintenance/workflow-control-two-dimensions.md`).
