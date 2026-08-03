<!-- Maintenance-route planning record. -->
# Maintenance change — `adapter-responsibility-boundaries`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `all profiles`, `reference-impl/java-micronaut-jena`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Define adapter responsibilities explicitly and enforce
  the Java profile's adapter dependency boundary.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | The change constrains adapter realization only; no feature response or outcome changes. |
| Action ordering and sync deduplication | preserved | No concept, sync, dispatch, or action-chain implementation changes. |
| Flow-token lineage | preserved | Primary adapters continue to enter through `rootAction()` and await an authored response. |
| Storage/retention semantics | n/a | No storage implementation or configuration changes. |

## Responsibility boundary

| Role | May do | Must not do |
|---|---|---|
| Primary adapter | Decode and validate transport syntax, normalize authentication/credentials, invoke one declared flow root, await an authored result, encode transport output. | Import or invoke concepts/syncs, access business persistence or action logs, choose a domain branch, or translate a domain outcome into a response. |
| Secondary adapter | Translate a declared port operation, credentials, protocol payloads, provider errors, and provider-specific technical acknowledgement. | Decide business policy/outcomes, invoke concepts/syncs, or hide observable retry/idempotency/ordering/delivery semantics. |
| Engine | Provide generic dispatch, action logging, transactions, scheduling, and provenance. | Distinguish a domain route, outcome, concept, or business field. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | Clarify primary/secondary adapter responsibility and transport-only exception boundaries in the ports/adapters overlay and Java profile code style. |
| Profile configuration or deployment files | no | No configuration or deployment changes. |
| Engine/runtime implementation | no | No production runtime behavior changes. |
| Profile tests | yes | Extend `LegibleArchitectureRulesTest` with adapter dependency-boundary regression coverage. |
| UC artefact chain | no | Existing contracts and feature artefacts remain unchanged. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Adapters cannot depend on concepts, syncs, or Jena persistence APIs | architecture | `LegibleArchitectureRulesTest` | pass | `mvn -f reference-impl/java-micronaut-jena/pom.xml -Dtest=LegibleArchitectureRulesTest test` (18 tests, 2026-08-03) |
| Primary adapters use only the narrow flow-entry/response engine API | architecture | `LegibleArchitectureRulesTest` | pass | `mvn -f reference-impl/java-micronaut-jena/pom.xml -Dtest=LegibleArchitectureRulesTest test` (18 tests, 2026-08-03) |
| Diagnostic infrastructure is excluded from the primary-adapter boundary | architecture | `LegibleArchitectureRulesTest` | pass | Generated `DebugController` definitions excluded by fully qualified name; focused suite passed (2026-08-03) |
| Full CLAD artefact pipeline remains intact | artefact | `python3 quality-gate/verify_artefacts.py` | pass | `UC-00-login` Stage 05 sequence passed (2026-08-03) |

## Rollback boundary

Revert the adapter-boundary documentation and the new ArchUnit rules together.
Do not alter feature artefacts or introduce adapter waivers merely to retain
existing implementation behavior.

## Gates

### Design gate

The human reviews the role table, allowed narrow engine API, non-goals, and
test matrix before documentation or Java architecture-test changes. Approve
with:

```bash
./clad approve-maintenance adapter-responsibility-boundaries design
```

### Evidence gate

The human reviews the completed architecture-test and artefact-pipeline
evidence before commit. After approval, set Status to `closed` and commit the
record with the implementation.

## Notes

- The Java enforcement is structural: it blocks prohibited dependencies and
  preserves the existing no-branch rule. It cannot prove semantic absence of
  domain policy in otherwise permitted adapter code.
- Transport syntax errors and protocol mechanics remain permitted; any branch
  outside that boundary requires an explicit reviewable waiver.