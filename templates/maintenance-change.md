<!-- Maintenance-route planning record. Copy to maintenance/<change-name>.md. -->
# Maintenance change — `<change-name>`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `<platform | mixed>`
- **Status:** `<draft | active | closed>` (`draft` until design approval,
  `active` while implementing, `closed` after evidence approval)
- **Affected profile(s):** `<reference-impl/<profile> | all profiles>`
- **Feature-contract impact:** `<preserved | re-entered>`
- **Design gate:** `<pending | approved>`
- **Evidence gate:** `<pending | approved>`
- **Change summary:** `<one sentence>`

## Contract impact

State whether each invariant is preserved, deliberately changed, or not
applicable. A deliberate change requires re-entry into the earliest affected
feature stage.

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `<preserved | changed | n/a>` | <how established> |
| Action ordering and sync deduplication | `<preserved | changed | n/a>` | <how established> |
| Flow-token lineage | `<preserved | changed | n/a>` | <how established> |
| Storage/retention semantics | `<preserved | changed | n/a>` | <how established> |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes \| no | <which invariant or document> |
| Profile configuration or deployment files | yes \| no | <which setting or deployment surface> |
| Engine/runtime implementation | yes \| no | <which classes> |
| Profile tests | yes \| no | <which tests> |
| UC artefact chain | yes \| no | <earliest re-entry stage, or why unchanged> |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| <invariant> | unit \| integration \| flow-regression \| smoke | <command or class> | pending \| pass | <result or link> |

## Gates

### Design gate

The human reviews contract impact, non-goals, and the test matrix before a
maintenance-scoped implementation or deployment file changes. Approve with
`./clad approve-maintenance <change-name> design`, then set Status to `active`.

### Evidence gate

The human reviews the completed test matrix and runtime evidence before commit.
After approval, set Status to `closed` and commit the record with the change.

## Notes

- <compatibility, rollback, or open questions>