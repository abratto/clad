# Maintenance change — `testing-runtime-evidence`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `mixed`
- **Status:** `closed`
- **Affected profile(s):** `all profiles`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Bind each Acceptance-Spec scenario to machine-produced runtime evidence (token chain, status, body, durable read-back) at Stage 05, and add a release profile that enforces mutation and durable checks where they apply.
- **Dependent re-entry:** `none`

## Why

Two testing-discipline gaps: (A) a green flow test plus a hand-assembled `trace.md`
do not prove the *running app* produced the approved chain/status/body — the
evidence is predicted or assembled, not produced; and (B) mutation and durable
checks can be skipped by local configuration with no visible release-grade
qualification (`mutation.require=false`).

## Mechanism

- **Evidence emitter.** `dev.legible.engine.EvidenceWriter#write` serializes the
  latest archived flow (`SyncEngine.archiver().buffer().latest()` +
  `DebugApi.flow`) plus `test` and optional `readback` to
  `<dir>/<scenario>.json` (dependency-free JSON).
- **Assembly.** `capture_observations.py#observation` extracts the runtime token
  chain and the terminal `status`/`body` (and `readback`) from each payload;
  `--out` writes `acceptance-evidence.json`.
- **Comparison.** `verify_acceptance_evidence.py#main` (blocking at Stage 05)
  compares each scenario's evidence to the frozen spec via
  `acceptance_evidence.py#compare` (chain, status, body fields, persistent
  read-back); a legacy `verification-trace.md` feature is grandfathered.
- **Release profile.** `verify_release_profile.py#main` reads
  `release.enforce`; when true it requires `mutation.command` + `mutation.require`
  and (persistent) a durable proof. Wired project-level in `verify_artefacts.py`
  and CI; self-activating (SKIPs for a template).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Evidence compares to the frozen spec; no contract change |
| Action ordering and sync deduplication | `preserved` | Unchanged |
| Flow-token lineage | `preserved` | Evidence reads the archived token chain |
| Storage/retention semantics | `preserved` | Read-back is a read; no write |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `TESTING.md`, `DELIVERY.md`, 05 CONTEXT, acceptance-spec template |
| Profile configuration or deployment files | yes | `clad.properties` `release.enforce`; `ci.yml` evidence + release steps |
| Engine/runtime implementation | yes | `EvidenceWriter` (engine); flow-test emitters (test code) |
| Profile tests | yes | `test_acceptance_evidence.py`, `test_release_profile.py`; example flow tests |
| UC artefact chain | yes | Stage 05 gains `acceptance-evidence.json` + `verify_acceptance_evidence` |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| evidence matches spec → pass | unit | `test_acceptance_evidence.py::test_matching_evidence_passes` | pass | suite green |
| wrong chain/status/body → fail | unit | `...::test_wrong_chain_fails`, `test_wrong_status_fails`, `test_missing_body_field_fails` | pass | suite green |
| missing evidence fails; legacy grandfathered | unit | `...::test_missing_evidence_fails`, `test_legacy_feature_is_grandfathered` | pass | suite green |
| persistent requires read-back | unit | `...::test_persistent_requires_readback`, `test_persistent_with_readback_passes` | pass | suite green |
| release profile enforces mutation + durable | unit | `test_release_profile.py` | pass | suite green |
| end-to-end: java-legible flow tests → evidence → spec | integration | `mvn test -pl java-legible` + `capture_observations` + `verify_acceptance_evidence` (CI) | pass | CI job |
| full gate | unit | `python3 -m pytest quality-gate/tests -q` | pass | 593 passed |

## Gates

Design and evidence gates approved; record closed after commit.

## Notes

- Forward-only: a feature with a legacy `verification-trace.md` and no evidence
  is grandfathered; new features must produce evidence at Stage 05.
- Browser (Playwright) and property-based tiers are deferred; the evidence
  contract is language-neutral JSON so a browser/property profile can emit it.
