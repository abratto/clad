# Maintenance change — `concept-maintenance-promotion`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `all profiles`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Give the R20 maintenance route a first-class, tooled path to publish an additive change to a canonical shared concept from a feature that is not the concept's current source, and link that corpus edit to the dependent feature re-entry.
- **Dependent re-entry:** `none`

## Why (experiment-found)

A behavioural change that adds an outcome or field to a **shared concept** has two
halves with different owners: the canonical concept (system scope) and the flow
that consumes it (one feature). `promote-concepts` correctly lets only the
concept's **current source** write the canonical entry (R22 order rule,
`stamp_provenance`), which is by definition the *last* extender — so the feature
that owns the flow is *necessarily* not the current source. `CONCEPTS.md` already
names the escape hatch: "route that corpus edit through the R20 maintenance
route". But there was no tooling for it — a maintainer hand-edited the canonical
`.concept.md`, so `extended-by` provenance and the `_promotions/` receipt the
flow feature needs were never stamped, and `verify_concept_corpus_current` could
fail on the mismatch. This change makes the sanctioned route executable without
relaxing R22 (a frozen proposal still may not roll the corpus back).

## Mechanism

`promote_concepts.py` gains a `--maintenance <change-name>` mode. It is the same
promotion pipeline as `--feature`, with the trust anchor changed from *"this
feature is the concept's current source"* to *"an approved maintenance change
names this feature as the proposer"*:

- **Trust anchor.** Reads `maintenance/<change-name>.md`; requires
  `Design gate: approved` and a `## Concept proposals` list of
  `<Name>: <feature>/stages/02_concepts/output/<Name>.concept.md`. The feature's
  Gate 2 is **not** required (the maintenance design gate is the review of record
  for the corpus edit) — `promote_concepts.py:None` (new branch in `main`).
- **Provenance.** Appends the proposing feature to the canonical `extended-by`
  history via the existing `stamp_provenance` / `_with_history`
  (`promote_concepts.py:206`, `:174`), using new order-aware helper
  `stamp_provenance_maintenance` that authorises the append from the maintenance
  gate instead of current-source equality.
- **Receipt.** Writes `_promotions/<feature>.md` exactly as a normal promotion
  (`promote_concepts.py:588`), so `verify_concept_corpus_current`'s
  history⇔receipt check (`verify_concept_corpus_current.py:139`) passes.
- **Additivity is unchanged.** The same `verify_concept_additivity` /
  `concept_remodel` drop checks run (`promote_concepts.py:508`): an additive
  outcome/field promotes; a drop/restate is refused unless the proposal is a
  `remodel` with migration notes + consent. R22's roll-back protection is intact.
- **Idempotent.** Re-running at the same proposal content is a no-op.

## Concept proposals

(none — this change is the mechanism itself, not a concept extension)

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No action changes; only *who may publish* a canonical concept edit widens, under a maintenance gate |
| Action ordering and sync deduplication | `preserved` | Unchanged; no sync surface |
| Flow-token lineage | `preserved` | Unchanged |
| Storage/retention semantics | `preserved` | Unchanged |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `CONCEPTS.md` + `ITERATIVE_CHANGES.md` §7: name the tooled route |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | no | — |
| Profile tests | yes | `quality-gate/tests/` regression cases (below) |
| UC artefact chain | no | The dependent feature re-enters via its own `_changes/` record, linked by `Dependent re-entry` |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| `--maintenance` appends `extended-by`, writes receipt, corpus check passes | unit | `test_promote_maintenance.py::test_maintenance_promote_appends_and_receipts` | pass | `pytest` green (541 total) |
| `--maintenance` refuses a non-additive drop | unit | `test_promote_maintenance.py::test_maintenance_promote_refuses_drop` | pass | `pytest` green (541 total) |
| `--maintenance` refuses without an approved design gate / proposals list | unit | `test_promote_maintenance.py::test_maintenance_promote_requires_design_gate` | pass | `pytest` green (541 total) |
| evidence gate requires a linked re-entry record to be closed | unit | `test_maintenance_readiness.py::test_dependent_reentry_must_be_closed` | pass | `pytest` green (541 total) |
| full gate | unit | `python3 -m pytest quality-gate/tests -q` | pass | `pytest` green (541 total) |

## Gates

### Design gate

The human reviews contract impact, non-goals, and the test matrix before a
maintenance-scoped implementation or deployment file changes. Approve with
`./clad approve-maintenance concept-maintenance-promotion design`, then set Status to `active`.

### Evidence gate

The human reviews the completed test matrix and runtime evidence before commit.
After approval, set Status to `closed` and commit the record with the change.

## Notes

- Backward-compatible: `--feature` promotion is unchanged. `--maintenance` is an
  additional, opt-in entry point.
- Non-goal: relaxing R22. A feature that is not the current source still may not
  call `--feature` promotion; only an approved maintenance record authorises the
  append.
- Rollback: remove the `--maintenance` branch; existing corpora are unaffected.
