# Maintenance change — `additivity-reentry-baseline`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `all profiles`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Additivity compares a re-entering feature's proposal (state and contract) to its own last committed version, not the moving canonical, so a canonical extension by a later feature no longer forces edits to earlier features' frozen proposals.
- **Dependent re-entry:** `none`

## Why (experiment-found)

Finding 32: after Change A promoted `title` into canonical `Reserving`, re-entering
UC-02 surfaced that its **frozen** Stage-02 proposal, data model, and contract
were now "non-additive" against the new canonical — the proposal "dropped" lines
(`title`, `listForDay`) a *later* feature (UC-03) had added after it. The check
`verify_concept_additivity` computed `dropped = current_canonical − proposal`,
which cannot distinguish "a line I had and removed" from "a line added after me",
so every earlier feature looked broken whenever a later one extended the concept.
Nothing declared or sequenced that dependency; it surfaced as cryptic blocking
errors mid-re-entry.

## Mechanism

`dropped_state_lines` and `dropped_contract_terms` take a `base` (default
`origin/main`) and read the proposal's **own committed prior version** with
`git show <base>:<path>` (`verify_concept_additivity.py:dropped_state_lines`,
`:dropped_contract_terms`, `:_git_show`); when that blob does not exist (first
authoring) they fall back to the current canonical — the previous behaviour,
byte-for-byte. `verify_concept_additivity.py` threads `--base` through both arms
and through `concept_remodel.unauthorised_drops[_additive]`. `promote_concepts.py`
is unchanged: promotion still compares to the canonical because it guards
against rolling the corpus back (a different question).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Additivity is unchanged on first authoring; only a re-entry's baseline moves |
| Action ordering and sync deduplication | `preserved` | Unchanged |
| Flow-token lineage | `preserved` | Unchanged |
| Storage/retention semantics | `preserved` | Unchanged |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `CONCEPTS.md` "State baselines" |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | no | — |
| Profile tests | yes | `quality-gate/tests/test_additivity_baseline.py` (5 cases) |
| UC artefact chain | no | Behaviour change to a stage check; no UC artefact edited |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| re-entry proposal lacking a later-canonical line passes | unit | `test_additivity_baseline.py::ReentryBaselineTests::test_reentry_lacking_a_later_canonical_line_passes` | pass | suite green |
| re-entry dropping its own prior line fails | unit | `...::test_reentry_dropping_its_own_prior_line_fails` | pass | suite green |
| no committed baseline falls back to canonical | unit | `...::test_without_a_committed_baseline_falls_back_to_canonical` | pass | suite green |
| contract arm: re-entry lacking a later action passes | unit | `...::ReentryContractBaselineTests::test_reentry_contract_lacking_a_later_action_passes` | pass | suite green |
| contract arm: re-entry dropping its own outcome fails | unit | `...::test_reentry_contract_dropping_own_outcome_fails` | pass | suite green |
| full gate | unit | `python3 -m pytest quality-gate/tests -q` | pass | 546 passed |

## Gates

### Design gate

Approve with `./clad approve-maintenance additivity-reentry-baseline design`,
then set Status to `active`.

### Evidence gate

Approve with `./clad approve-maintenance additivity-reentry-baseline evidence`
after the test matrix is green; then set Status to `closed`.

## Notes

- Backward-compatible: first authoring behaves exactly as before; promotion
  still guards rollback against the canonical.
- Non-goal: weakening additivity. A feature that removes a line it carried still
  fails, and the maintenance/remodel paths are unchanged in intent.
- Rollback: drop `--base`; the checks revert to the canonical baseline.
