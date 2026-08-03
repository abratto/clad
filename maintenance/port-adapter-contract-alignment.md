# Maintenance change — `port-adapter-contract-alignment`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `active`
- **Affected profile(s):** `all profiles`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Align generic port documentation, templates, and validation with the primary/secondary adapter overlay.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | No feature artefact or response contract changes; the gate validates declared port evidence consistently. |
| Action ordering and sync deduplication | preserved | No runtime action-chain, sync, or engine change. |
| Flow-token lineage | preserved | No flow-token data or implementation change. |
| Storage/retention semantics | n/a | No storage implementation or configuration change. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | Generalize port and primary-adapter documentation; retain HTTP-specific Java profile documentation. |
| Profile configuration or deployment files | no | No profile configuration or deployment change. |
| Engine/runtime implementation | no | Update only the quality-gate validator. |
| Profile tests | yes | Add deterministic Python fixtures for inbound and outbound port validation. |
| UC artefact chain | no | Existing HTTP example artefacts remain valid; no feature contract changes. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| A populated port specification satisfies the validator for an inbound contract | fixture | `python3 -m unittest quality-gate/tests/test_port_spec_contract.py` | pass | Inbound response-shape and `@contract` fixture passed. |
| Outbound port entries do not require HTTP response-shape or Gherkin contract evidence | fixture | `python3 -m unittest quality-gate/tests/test_port_spec_contract.py` | pass | Outbound adapter-boundary fixture passed. |
| Missing required port-entry fields and missing inbound evidence fail | fixture | `python3 -m unittest quality-gate/tests/test_port_spec_contract.py` | pass | Missing evidence fixture failed as required. |
| Existing quality-gate regressions remain green | regression | `python3 -m unittest discover -s quality-gate/tests` | pass | 12 tests passed. |
| Current CLAD artefact chain remains intact | artefact | `python3 quality-gate/verify_artefacts.py` | pass | Artefact pipeline passed. |

## Gates

### Design gate

Port specifications are a list of directional entries. Every entry declares a
name, direction, adapter type, owner, source contract, observable semantics,
and test evidence. Inbound entries retain Stage 04b response-shape and Stage
04c contract-scenario requirements. Outbound entries instead require
adapter-boundary evidence; they must not be forced into an HTTP/JSON Gherkin
shape. Missing required entry fields and missing inbound/outbound evidence
remain failures.

### Evidence gate

Review focused fixture coverage for successful inbound and outbound entries,
retained failure cases, documentation alignment, the full quality-gate fixture
suite, and the artefact pipeline.

## Notes

- The change does not generalize Java/Micronaut profile documentation that is
  intentionally HTTP-specific.
- The Java profile and its concurrency benchmark are out of scope because no
  engine or profile source changed.
- Rollback restores the prior template and validator contract; focused fixtures
  guard the new directional contract.