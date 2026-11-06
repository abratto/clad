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
- **Dependent re-entry:** `<none | features/UC-XX-<slug>/_changes/<name>.md>`
  (the feature iterative change, if any, that re-enters the flow this corpus
  edit enables; when set, the evidence gate requires it closed)

## Mechanism

For a semantic change (one that touches an engine/profile code path), state
**how** the change works, not just what it does — and cite the code path each
claim rests on: `path/to/File.java:LINE` or `File#symbol`. A mechanism claim
with no citation is how a wrong explanation survives into the next author's
head (the flow-pin record claimed the engine "never re-evaluates"; it does —
`reference-impl/legible-engine/src/main/java/dev/legible/engine/SyncEngine.java:266`).
The citation is what would have caught it. Omit this section only for a change
with no engine/profile behaviour (e.g. a pure documentation or configuration
rename).

- <claim> — `<file>:<line>` or `<File>#<symbol>`.

## Concept proposals

Only for a maintenance change that edits a **canonical shared concept** from a
feature that is not the concept's current source (an additive extension the
promotion order would otherwise refuse). Name the feature whose re-derived
Stage-02 proposal to promote; omit the section for every other change.

- `<Name>: features/UC-XX-<slug>/stages/02_concepts/output/<Name>.concept.md`

Publish with `./clad promote-concepts --maintenance <change-name>` (no `--feature`):
it appends the feature to the concept's `extended-by` history and writes the
`_promotions/` receipt under this change's approved design gate, applying the
same additivity rules as a normal promotion.

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