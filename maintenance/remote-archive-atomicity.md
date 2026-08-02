# Maintenance change — `remote-archive-atomicity`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `active`
- **Affected profile(s):** `reference-impl/java-micronaut-jena`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Make remote completed-flow archival a single atomic storage operation.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | No concept or Web action changes. |
| Action ordering and sync deduplication | preserved | Archival occurs only after a completed flow. |
| Flow-token lineage | preserved | Every ordinary and RDF-star record for a flow moves or deletes together. |
| Storage/retention semantics | preserved | Archive-enabled moves the complete flow; archive-disabled deletes the complete flow. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | Define atomic remote archival guarantee. |
| Profile configuration or deployment files | no | No backend selection or deployment change. |
| Engine/runtime implementation | yes | Lower remote archival to one atomic operation or prove equivalent Fuseki transaction semantics. |
| Profile tests | yes | Add a focused remote atomicity/failure-injection test. |
| UC artefact chain | no | Observable actions, outcomes, and ordering are unchanged. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Remote archival cannot leave ordinary and RDF-star flow data split | integration | `StorageArchiveFlowTest.remoteStorageRollsBackEveryOperationInAFailedUpdateRequest` | pass | Fuseki rejected a trailing `LOAD` and retained the preceding flow data. |
| Archive and delete policies retain their current behavior | integration | `StorageArchiveFlowTest` | pass | Local and remote archive/delete cases passed. |
| Login contract remains unchanged | flow-regression | canonical `test.command` | pass | Maven suite passed: 69 tests, 0 failures, 0 errors. |

## Gates

### Design gate

Use one multi-operation SPARQL update request for standard and RDF-star flow data. The remote HTTP client's transaction lifecycle is local-only; Fuseki request atomicity is established by the failure-path test.

### Evidence gate

Review the focused remote test, canonical profile verification, and any required Fuseki runtime evidence.

## Notes

- Do not claim HTTP-request batching alone is atomic without test or server evidence.
- Rollback is the prior remote archive implementation.