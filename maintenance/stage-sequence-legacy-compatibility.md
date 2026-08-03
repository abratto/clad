<!-- Maintenance-route planning record. -->
# Maintenance change — `stage-sequence-legacy-compatibility`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `active`
- **Affected profile(s):** `all profiles`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Make quality-gate stage sequencing recognize documented
  pre-split Stage 04 evidence while retaining strict child-stage ordering for
  new and actively re-entered work.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | Only quality-gate routing and compatibility recognition change; feature artefacts and runtime code are untouched. |
| Action ordering and sync deduplication | preserved | No concept, sync, or dispatch implementation changes. |
| Flow-token lineage | preserved | No Stage 05 trace content or runtime token implementation changes. |
| Storage/retention semantics | n/a | No storage surface changes. |

## Compatibility boundary

- A completed feature with legacy `04d_concept-tdd/output/concept-tdd.md` and
  `04e_sync-tdd/output/sync-tdd.md` may satisfy the historical child-stage
  evidence only when no current child-stage re-entry is active.
- A documented historical green summary may satisfy its immediately preceding
  missing red artefact only as migration evidence for a completed legacy flow.
- New features and active iterative re-entry remain strict: they require real
  child-stage outputs in canonical order. The gate must fail unexplained
  partial child-stage histories.
- No placeholder child-stage output may be fabricated to satisfy the guard.

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | Document migration-only Stage 04 compatibility in `methodology/implementation/STAGES.md`. |
| Profile configuration or deployment files | no | No configuration or deployment change. |
| Engine/runtime implementation | yes | Update `quality-gate/verify_stage_sequence.py` and `quality-gate/verify_artefacts.py` target selection. |
| Profile tests | yes | Extend `quality-gate/tests/test_stage_workflow.py` with legacy and iterative re-entry regression cases. |
| UC artefact chain | no | Feature contracts are preserved; legacy evidence is interpreted without rewriting feature outputs. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Fully completed pre-split features remain valid | unit | `test_stage_workflow.py` legacy completed-flow fixture | pass | `python3 -m unittest discover -s quality-gate/tests` (2026-08-03) |
| Legacy parent Stage 04 evidence maps only to historical child stages | unit | `test_stage_workflow.py` parent `concept-tdd.md` / `sync-tdd.md` fixture | pass | `python3 -m unittest discover -s quality-gate/tests` (2026-08-03) |
| Active re-entry ignores historical later Stage 05 output | unit | `test_stage_workflow.py` active `_changes/` fixture | pass | `python3 -m unittest discover -s quality-gate/tests` (2026-08-03) |
| New partial child-stage history remains invalid | unit | `test_stage_workflow.py` unexplained child-stage fixture | pass | `python3 -m unittest discover -s quality-gate/tests` (2026-08-03) |
| Fresh red/green routing remains strict | unit | existing fresh-skeleton routing test | pass | `python3 -m unittest discover -s quality-gate/tests` (2026-08-03) |
| Full artefact pipeline remains intact | integration | `python3 quality-gate/verify_artefacts.py` | pass | `UC-00-login` Stage 05 sequence passed (2026-08-03) |
| Quality-gate regression suite passes | unit | `python3 -m unittest discover -s quality-gate/tests` | pass | 17 tests passed (2026-08-03) |

## Rollback boundary

Revert only the compatibility interpretation in `verify_stage_sequence.py` and
the active-re-entry target selection in `verify_artefacts.py`, together with
their regression tests and Stage 04 documentation. Do not alter legacy feature
outputs, create placeholder child-stage artefacts, or re-run completed feature
pipelines as part of rollback.

## Gates

### Design gate

The human reviews the compatibility boundary, strictness guarantees, rollback
boundary, and test matrix before quality-gate implementation changes. Approve
with:

```bash
./clad approve-maintenance stage-sequence-legacy-compatibility design
```

### Evidence gate

The human reviews the completed regression matrix and artefact-pipeline
evidence before commit. After approval, set Status to `closed` and commit the
record with the implementation.

## Notes

- This is platform maintenance: it preserves the feature contract and must not
  rewrite Stage 04 artefacts solely to satisfy a newer validator.
- The compatibility path is intentionally narrow and migration-only; it must
  not permit a new feature or re-entry to skip a red or green child stage.