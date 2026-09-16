# Maintenance change — `engine-empty-safe-aggregate`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `reference-impl/legible-engine` (`where` frame evaluation), all profiles via inheritance
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved` (human in-conversation: "why not fix the engine root" → adopt the root fix)
- **Evidence gate:** `approved` (test matrix below)
- **Change summary:** Make frame-set aggregation **empty-safe**: a `CollectBy` clause reached with an empty frame set now emits one frame carrying the empty list, instead of the rule being dropped. A zero-item collection is a value, not an absence.

## Why (experiment-found)

The conduit rebuild experiment's UC-07 (`View Comments`) required an article with **no comments** to answer `200 {"comments": []}`. The declarative shape — `fanOut` over the thread's comments, then `collectBy` to gather the thread's author ids — produced **zero frames** when the thread was empty, and `WhereEvaluator.evaluate` returned early on the empty set **before** the `CollectBy` clause ran, so the enrichment syncs never fired and the join never completed: the empty-thread response was **unreachable**. Every design-time gate (parity, route filters, cycle/overlap, declarative, transition coverage) passed; only Stage-05 runtime back-trace caught it (the gates verify structure, not cardinality).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No flow/outcome changed; reactor green |
| Action ordering and sync deduplication | `preserved` | Clause order unchanged; only the empty-set short-circuit removed |
| Flow-token lineage | `preserved` | Read/frame evaluation only |
| Storage/retention semantics | `preserved` | No storage change |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `WhereEvaluator` javadoc/comments |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | yes | `WhereEvaluator.evaluate` — seed one empty frame before a `CollectBy` on an empty frame set; drop the early return so a later aggregate still runs |
| Profile tests | yes | `EvalEmptyAggregateTest` (new) |
| UC artefact chain | no (additive) | UC-07 re-derives its syncs to the empty-safe shape; no retrofit elsewhere |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| `collectBy` over zero frames emits one frame with an empty list | unit | `mvn -f reference-impl/pom.xml -pl legible-engine test` (`EvalEmptyAggregateTest`) | pass | 1 case |
| Existing engine/collect/join semantics unaffected | unit | same (28 prior engine tests) | pass | `Tests run: 30, Failures: 0` |
| Stocked profiles unaffected | unit | `mvn -f reference-impl/pom.xml test` | pass | BUILD SUCCESS |
| Gate pipeline intact | integration | `python3 quality-gate/verify_artefacts.py` | pass | artefact pipeline intact |

## Gates

### Design gate

Approved in-conversation (the human questioned the reviewer's initial preference for a
feature-local workaround over the engine root fix; the root fix was adopted).

### Evidence gate

Recorded from the executed reactor run; Status `closed` with the change commit.

## Notes

- `collectBy` now gathers in **frame-iteration order** (not sorted), so two parallel `collectBy` clauses over the same frame set stay positionally aligned (a join consumer like `Following.isFollowing` zips two such lists). Per-frame `collect`/`distinct`/`scan` keep their deterministic ordering (`sortedValues`/`distinctSorted`).
- This is the **collection** half of the earlier join/collect work (`engine-declarative-join-collect`); the empty set was the remaining hole.
- Downstream: the conduit rebuild fork inherits the engine file and re-derives UC-07's `commentIds`/`authorIds` gathering to use frame-set `collectBy` (one list-shaped `isFollowing`/`profilesOf` call).
