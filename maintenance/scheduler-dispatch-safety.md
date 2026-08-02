# Maintenance change — `scheduler-dispatch-safety`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `draft`
- **Affected profile(s):** `reference-impl/java-micronaut-jena`
- **Feature-contract impact:** `preserved`
- **Design gate:** `pending`
- **Evidence gate:** `pending`
- **Change summary:** Improve scheduler targeting, pagination, and concurrency while preserving observable action order and flow lineage.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | Dispatcher scheduling must not change concept or Web outcomes. |
| Action ordering and sync deduplication | preserved | Every eligible invocation runs once; no invocation is skipped or duplicated. |
| Flow-token lineage | preserved | Each dispatched invocation remains associated with its originating flow. |
| Storage/retention semantics | n/a | This change does not alter storage retention. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | Document fairness, pagination, and concurrency invariants. |
| Profile configuration or deployment files | no | No deployment setting change planned. |
| Engine/runtime implementation | yes | Revise scheduler/dispatcher selection and execution mechanics. |
| Profile tests | yes | Add deterministic pagination, concurrency, and exactly-once tests. |
| UC artefact chain | no | Existing observable action choreography must remain unchanged. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Pending invocations beyond one query page are eventually dispatched | integration | scheduler pagination test | pending | pending |
| Concurrent dispatch does not duplicate an invocation | integration | scheduler concurrency test | pending | pending |
| An expired claim becomes eligible for dispatch again | integration | scheduler lease-recovery test | pending | pending |
| A dispatched invocation retains its original flow token | integration | flow-lineage scheduler test | pending | pending |
| Existing login action order remains unchanged | flow-regression | canonical `test.command` | pending | pending |

## Gates

### Design gate

For every concept-action poll, the dispatcher claims at most 100 eligible
invocations in ascending action-IRI order. Eligibility is an invocation with
no `:outcome` and either no dispatcher claim or an expired claim. A single
SPARQL update assigns the claims before any invocation is processed, so
concurrent dispatch loops cannot both acquire the same invocation.

Each claim carries an opaque dispatcher-generated token and a lease expiry 30
seconds after acquisition. The dispatcher reads back only actions bearing its
token, retaining their existing `:flow` value. A successful completion
supersedes the claim through the existing `:outcome` record. If a dispatcher
stops before completion, another loop may reclaim the action after the lease
expires. Claims are scheduler metadata only: they create no flow token and do
not change concept outcomes, sync rules, or causal action order.

Tests must prove bounded pagination, concurrent exactly-once acquisition,
lease recovery, flow-token preservation, and the existing login regression.

### Evidence gate

Review deterministic scheduler tests, concurrency evidence, and canonical profile verification.

## Notes

- Any change to observable action order, outcomes, or flow lineage requires feature-stage re-entry instead of this maintenance route.
- Design gate is approved; activate this record only after the active archive-atomicity change closes.
- Rollback restores the prior scheduler implementation.