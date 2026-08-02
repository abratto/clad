# Maintenance change — `storage-backend-reliability`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `active`
- **Affected profile(s):** `reference-impl/java-micronaut-jena`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Make configured remote storage selection and completed-flow retention consistent across local and remote Jena backends.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | Existing UC-00 Cucumber scenarios remain the regression oracle. |
| Action ordering and sync deduplication | preserved | Storage and configuration changes do not alter dispatcher or sync logic. |
| Flow-token lineage | preserved | Archival moves or deletes every triple associated with a completed flow. |
| Storage/retention semantics | changed | `engine.archive.flows=false` must delete completed flows for local and remote storage; completed flows must not be split between active and archive graphs. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | Document supported configuration and whole-flow archival semantics. |
| Profile configuration or deployment files | yes | Map Compose configuration to the remote Fuseki backend and endpoint; point the canonical test command at the shipped reference profile. |
| Engine/runtime implementation | yes | Update dataset configuration resolution and remote archival behavior. |
| Profile tests | yes | Add configuration and local/remote storage conformance tests. |
| UC artefact chain | no | Action outcomes, sync rules, flow lineage, and HTTP contract are preserved. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Compose-style configuration selects remote storage | unit | `CladDatasetFactory` configuration test | pass | `CladDatasetFactoryTest`: Compose environment selects `RemoteStorage`; missing endpoint or partial credentials fail closed. |
| Archive-enabled storage moves a complete flow | integration | local and embedded-Fuseki storage conformance tests | pass | `StorageArchiveFlowTest`: 2 tests passed under the canonical suite. |
| Archive-disabled storage deletes a complete flow | integration | local and embedded-Fuseki storage conformance tests | pass | `StorageArchiveFlowTest`: 2 tests passed under the canonical suite. |
| A completed flow is never split across active/archive graphs | integration | embedded-Fuseki storage conformance test | pass | `StorageArchiveFlowTest` verified ordinary and RDF-star records move or delete together. |
| Login outcomes and response contract are unchanged | flow-regression | profile Maven verification | pass | Canonical artefact gate and Maven suite: 68 tests passed. |
| Compose uses the configured remote service | smoke | Docker Compose startup and login request | pass | Fuseki healthy; app started with authenticated remote storage; `POST /login` returned a session token. |

## Gates

### Design gate

Scope excludes scheduler targeting, pagination, and dispatcher redesign. Those changes require a separate maintenance record because they need distinct scheduling and concurrency invariants.

### Evidence gate

Evidence will include the completed test matrix, the profile verification result, and Compose smoke output.

## Notes

- Fail closed on an invalid remote backend configuration; do not silently fall back to in-memory storage.
- Keep the storage abstraction's archive policy backend-neutral so local and remote implementations satisfy the same conformance tests.
- Rollback is the prior profile configuration and storage implementation; no feature artefact migration is required because the external contract is preserved.