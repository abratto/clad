# Maintenance change — `remote-resilience-and-security`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `draft`
- **Affected profile(s):** `reference-impl/java-micronaut-jena`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `pending`
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
| Rejected credentials fail clearly without local fallback | integration | authenticated embedded-Fuseki test | pending | pending |
| Unavailable remote endpoint fails within configured timeout | integration | `RemoteStorage` failure-path test | pending | pending |
| Write failures do not produce a false completion | integration | `RemoteStorage` failure-path test | pending | pending |
| Retry behavior cannot duplicate completed actions | integration | failure/retry test or explicit no-retry assertion | pending | pending |
| Login contract remains unchanged | flow-regression | canonical `test.command` | pending | pending |

## Gates

### Design gate

Choose timeout values, TLS policy, service-account configuration, and either a bounded idempotent retry design or an explicit no-retry policy.

### Evidence gate

Review failure-path tests, deployment configuration, and canonical profile verification.

## Notes

- Do not include real credentials in repository files or test output.
- Design gate is approved; activate this record only after the active archive-atomicity change closes.
- Rollback restores the existing remote client configuration.