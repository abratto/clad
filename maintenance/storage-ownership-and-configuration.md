# Maintenance change — `storage-ownership-and-configuration`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `reference-impl/java-micronaut-jena`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Eliminate silent local action-log storage when the remote Fuseki backend is selected and reject unsupported backend configuration.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | Storage wiring changes do not alter concept or Web behavior. |
| Action ordering and sync deduplication | preserved | One action-log backend is selected at bootstrap. |
| Flow-token lineage | preserved | All action-log consumers use the selected backend. |
| Storage/retention semantics | preserved | Existing backend-specific retention policy remains unchanged. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | State ownership rules and supported backend values. |
| Profile configuration or deployment files | yes | Validate backend type and configure the selected backend explicitly. |
| Engine/runtime implementation | yes | Remove or make fail-fast the remote backend's local `Dataset` stub. |
| Profile tests | yes | Add bootstrap ownership and unknown-backend tests. |
| UC artefact chain | no | Domain action contract is unchanged. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Remote backend cannot expose an unrelated writable local action log | unit | `CladDatasetFactoryTest.remoteBackendCannotExposeAnUnconnectedLocalDataset` | pass | Both factory and `RemoteStorage.dataset()` reject disconnected local Dataset access. |
| Unknown backend type fails during bootstrap | unit | `CladDatasetFactoryTest.unsupportedBackendTypeFailsClosed` | pass | Unsupported `engine.dataset.type` throws `IllegalStateException`. |
| Supported local and remote selections remain valid | unit | `CladDatasetFactoryTest` | pass | All five configuration tests passed. |
| Login contract remains unchanged | flow-regression | canonical `test.command` | pass | Canonical artefact gate and Maven suite passed. |

## Gates

### Design gate

Select the single supported injection boundary for action-log state and document any compatibility impact for direct `Dataset` injection.

### Evidence gate

Review configuration tests and canonical profile verification.

## Notes

- Invalid configuration must fail during bootstrap; never silently fall back to `tmemory`.
- Reopened after review found `RemoteStorage.dataset()` still returned a writable local stub; the stub is now removed and the direct API fails closed.
- Rollback restores the previous factory behavior.