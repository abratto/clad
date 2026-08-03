# Maintenance change — `implementation-parity-compact-matrix`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `active`
- **Affected profile(s):** `all profiles`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Extend implementation parity to parse valid compact Sync Contract Matrix completion notation.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | The gate only reads approved artefacts and does not modify application behavior. |
| Action ordering and sync deduplication | preserved | No runtime action-chain or synchronization behavior changes. |
| Flow-token lineage | preserved | No runtime flow data changes. |
| Storage/retention semantics | n/a | No storage or deployment changes. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | no | No profile contract change. |
| Profile configuration or deployment files | no | No configuration change. |
| Engine/runtime implementation | no | No application or reference-engine change. |
| Profile tests | no | Extend deterministic quality-gate parser fixtures. |
| UC artefact chain | no | Existing valid matrix artefacts remain unchanged. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Arrow-form matrix contracts still derive mechanical names | fixture | `python3 -m unittest quality-gate/tests/test_parser_regressions.py` | pass | Arrow matrix fixture passed. |
| Compact `Concept/action: [Outcome(...)]` contracts derive the leading outcome token | fixture | `python3 -m unittest quality-gate/tests/test_parser_regressions.py` | pass | Four `Web/handle: [Routed(...)]` contracts lowered to matching `WhenWebHandleRoutedThen...For...` classes. |
| Malformed compact matrix syntax remains rejected | fixture | `python3 -m unittest quality-gate/tests/test_parser_regressions.py` | pass | A missing colon between action and completion remains invalid. |
| Existing CLAD artefact and Java profile tests remain green | regression | canonical `test.command` | pass | Artefact gate and Maven suite passed: 73 tests, 0 JUnit failures/errors/skips. |

## Gates

### Design gate

Within a Sync Contract Matrix, parse `when` signatures as either the existing
arrow form `Concept/action: [ inputs ] => [ OUTCOME(fields) ]` or the compact
form `Concept/action: [Outcome(fields)]`. The matrix remains authoritative when
present; a valid compact row must not cause fallback to `## Rule`. For both
forms, derive the mechanical name from the leading completion identifier using
the existing PascalCase normalization. Reject any matrix row that does not
match either grammar. Preserve legacy Rule parsing, missing-spec checks,
filename/header checks, implementation-name checks, and the existing
ConceptAgent-only concept classification.

### Evidence gate

Review arrow, compact, and malformed fixture coverage plus the canonical
profile regression command.

## Notes

- This follows up `9ee4fc6`; it is intentionally limited to the remaining
  implementation-parity matrix grammar gap.
- Rollback restores the previous arrow-only matrix parser.