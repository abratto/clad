# Maintenance change — `red-green-test-continuity`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed` (`draft` until design approval, `active` while
  implementing, `closed` after evidence approval)
- **Affected profile(s):** `all profiles` (gate machinery + stage
  contracts; no engine/runtime code)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved` — human pre-approved in-conversation
  ("adopt T1+T2 now"); approved before any implementation started
- **Evidence gate:** `approved` (test matrix below; all rows pass)
- **Change summary:** Mechanize contracts T1 (red-for-the-right-reason:
  failure class recorded at red, asserted at green) and T2 (red→green
  test-file immutability: SHA-256 continuity table regenerated at the
  green stage via `verify_test_continuity.py`).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No artefact or runtime behaviour change; test-fidelity gates only |
| Action ordering and sync deduplication | `n/a` | Gate wiring in `clad_stages.py` does not touch ordering logic |
| Flow-token lineage | `n/a` | No engine change |
| Storage/retention semantics | `n/a` | No storage surface touched |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `methodology/implementation/TDD.md` — failure-class rider (T1) |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | no | — |
| Profile tests | no | quality-gate fixture tests are new, not profile tests |
| UC artefact chain | yes (contract only, no retrofit) | `templates/feature-skeleton/` 04d/04e red+green CONTEXTs (continuity section, failure-class requirement, green pre-conditions); `templates/test-intent-derivation-map.md` `## Test file continuity` sketch; `features/UC-00-login/stages/**` contract wording riders — UC-00 frozen outputs untouched, and `test_continuity` SKIPs for it by the absent-section convention so any pre-gate advance behaves exactly as before |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Continuity verifier: PASS on unchanged files, FAIL on drift/missing + routing instruction, SKIP on absent section | unit | `python3 -m unittest quality-gate.tests.test_test_continuity` | pass | 4 cases green (2026-09-14) |
| Existing quality-gate suite unaffected (90 total, was 86) | unit | `python3 -m unittest discover -s quality-gate/tests -t quality-gate/tests` | pass | `Ran 90 tests … OK` |
| Gate pipeline intact (check registration compiles; UC-00 skips by absence convention) | integration | `python3 quality-gate/verify_artefacts.py` | pass | artefact pipeline intact |
| Doc links stay green | unit | `python3 quality-gate/verify_links.py` | pass | `PASS  305 cross-reference link(s) checked, 105 docs scanned` |
| Reference reactor green | flow-regression | `mvn -f reference-impl/pom.xml test` | pass | `Tests run: 16, Failures: 0` BUILD SUCCESS |

## Gates

### Design gate

Approved in-conversation by the human (pre-approved: "adopt T1+T2 now")
before implementation. Recorded as `approved` here by the adopting agent
per instruction; no `approve-maintenance` ceremony available in the
conversation channel.

### Evidence gate

Reviewed by the human in-conversation after the test matrix ran green;
Status set to `closed` and the record committed with the change.

## Notes

- Skip-when-absent convention: features whose derivation maps predate
  the continuity section (UC-00-login, features without code) advance
  unchanged — no retrofit.
- T2's enforcement surface mirrors the Gate 3 content-hash mechanism
  (outer loop) one level down: red receipt → green recompute.
- No engine change, so no app/code re-validation needed in
  downstream profiles beyond their normal `test.command` gate.
