# Maintenance change — `remote-resilience-and-security`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `reference-impl/java-micronaut-jena`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Define secure credentials, transport, and failure behavior for remote Fuseki storage.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | Remote storage failures remain infrastructure failures, not new domain outcomes. |
| Action ordering and sync deduplication | preserved | No automatic retry may duplicate an action or sync completion. |
| Flow-token lineage | preserved | Failed remote writes must not be reported as completed flow effects. |
| Storage/retention semantics | preserved | Security and timeout handling do not alter retention policy. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | Document credential, TLS, timeout, and retry policy. |
| Profile configuration or deployment files | yes | Replace development-default credential posture with explicit deployment configuration. |
| Engine/runtime implementation | yes | Configure HTTP timeouts and safe authentication/transport validation. |
| Profile tests | yes | Cover rejected credentials, unavailable endpoint, and write failure behavior. |
| UC artefact chain | no | No domain action or response contract changes. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Rejected credentials fail clearly without local fallback | integration | `RemoteStorageTest.rejectedCredentialsStopAfterOneChallengeRetry` | pass | Controlled `401` endpoint rejects credentials after one challenge retry. |
| Unavailable remote endpoint fails within configured timeout | integration | `RemoteStorageTest.unavailableEndpointFailsWithoutRetryingTheWrite` | pass | Connection failure throws without writing; client connection timeout is five seconds. |
| Write failures do not produce a false completion | integration | `RemoteStorageTest` | pass | Rejected and unavailable writes leave no record in the remote Fuseki fixture. |
| Retry behavior cannot duplicate completed actions | integration | `RemoteStorageTest.rejectedCredentialsStopAfterOneChallengeRetry` | pass | Authenticator returns credentials once, bounding a rejected request to two attempts. |
| Login contract remains unchanged | flow-regression | canonical `test.command` | pass | Compose interpolation, artefact gate, and Maven suite passed. |

## Gates

### Design gate

Connection establishment times out after five seconds. Authentication is bounded to the initial challenge plus one credentialed retry; there is no retry after a completed remote update. Compose requires an explicit password. Internal Compose traffic uses private-network HTTP; externally hosted Fuseki must use HTTPS and a least-privilege service account.

### Evidence gate

Review failure-path tests, deployment configuration, and canonical profile verification.

## Notes

- Do not include real credentials in repository files or test output.
- Remains approved for activation after storage ownership closes with the direct remote Dataset stub removed.
- Rollback restores the existing remote client configuration.