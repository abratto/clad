<!-- Maintenance-route planning record. -->
# Maintenance change — `iterative-change-readiness-selection`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `all profiles`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Select the single active iterative-change matrix and
  ignore closed or superseded historical records during readiness validation.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | Only quality-gate record selection changes; no feature artefacts or runtime code change. |
| Action ordering and sync deduplication | preserved | The validator still blocks incomplete iterative changes; it only ignores non-active history. |
| Flow-token lineage | preserved | No action-chain or runtime implementation changes. |
| Storage/retention semantics | n/a | No storage surface changes. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | Document active-record selection and historical-record handling in iterative-change guidance. |
| Profile configuration or deployment files | no | No configuration or deployment changes. |
| Engine/runtime implementation | yes | Update `quality-gate/verify_iterative_change_readiness.py` selection logic. |
| Profile tests | yes | Add focused regression coverage for active, closed, and superseded `_changes` records. |
| UC artefact chain | no | Existing feature contracts remain unchanged. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| One active record is selected despite closed or superseded history | unit | `python3 quality-gate/tests/test_iterative_change_readiness.py` | pass | 4 tests passed, 2026-08-03 |
| No active record remains a hard failure | unit | `python3 quality-gate/tests/test_iterative_change_readiness.py` | pass | 4 tests passed, 2026-08-03 |
| Multiple active records remain a hard failure | unit | `python3 quality-gate/tests/test_iterative_change_readiness.py` | pass | 4 tests passed, 2026-08-03 |
| Existing quality-gate regression suite remains green | unit | `python3 -m unittest discover -s quality-gate/tests` | pass | 21 tests passed, 2026-08-03 |
| Full artefact pipeline remains intact | artefact | `python3 quality-gate/verify_artefacts.py` | pass | `UC-00-login` Stage 05 sequence passed, 2026-08-03 |

## Rollback boundary

Revert the readiness-validator selection logic, its regression tests, and the
iterative-change guidance together. Do not suppress failures for missing or
multiple active change records.

## Gates

### Design gate

The human reviews the active-record selection rule, retained failure modes, and
test matrix before quality-gate implementation changes. Approve with:

```bash
./clad approve-maintenance iterative-change-readiness-selection design
```

### Evidence gate

The human reviews the completed regression and artefact-pipeline evidence
before commit. After approval, set Status to `closed` and commit the record
with the implementation.

## Notes

- Explicit `--change-file` selection remains supported; it is an operator
  override and must still validate the selected record.
- This change addresses only false ambiguity from historical records. Missing
  stage evidence and unrelated feature defects remain blocking.