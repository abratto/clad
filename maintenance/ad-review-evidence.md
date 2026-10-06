# Maintenance change — `ad-review-evidence`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed` (`draft` until design approval, `active` while
  implementing, `closed` after evidence approval)
- **Affected profile(s):** all features (quality-gate scripts + the Stage 01b
  and 03a stage contracts in `templates/feature-skeleton`, mirrored in the
  worked example); no runtime profiles touched
- **Feature-contract impact:** `preserved` (advisory views only; the matrix
  never blocks, the drift check blocks only on staleness of a committed
  derived view — the `shared_triggers_current` pattern)
- **Design gate:** `approved` (human, in-conversation: "do it" — the deferred
  items from `ad-design-deepening` / `ad-process-domain`: persist the FR×DP
  matrix and the sync-information profile as canonical 03a outputs, wire the
  matrix at Gate-1 (01b) as well, add a per-feature D-read budget)
- **Evidence gate:** `approved`
- **Change summary:** Make the AD review's evidence durable and early:
  `generate_review_views.py` emits `fr-dp-matrix.md` and
  `sync-information-profile.md` as canonical, manifest-listed 03a outputs
  (drift-checked; the `pattern-d-summary` precedent); the FR×DP matrix check
  also runs advisively at Stage 01b so the reviewer sees it at Gate 1 where
  God-Object/duplication defects are cheapest to fix; `sync_information.py`
  gains a `--d-budget` (default 5) whose exceeding is an advisory finding.

## Mechanism

- **03a outputs.** The views are fully derived from Gate-1 artifacts (the
  matrix: usecase + chain tables + responsibility map; the profile: the 03
  sync pack), so a generator is the house shape:
  `generate_review_views.py --feature <root> [--write|--check]` reuses
  `verify_concept_matrix`'s builders and `sync_information`'s parser. The
  03a contract (template + example) gains a deterministic-generation-first
  step and the two files in its Outputs; the manifest (`expected_stage_outputs`
  reads the stage contract's Outputs) lists them; the worked example's 03a
  output gains both files. A stage check (`review_views_current`) blocks on
  staleness of a committed view (regenerate→compare, the `shared_triggers`
  drift pattern), skipping while absent (the manifest owns presence).
- **Matrix at 01b.** The same `_FR_DP_MATRIX` check joins Stage 01b's list —
  all three inputs exist by 01b (usecase ← 01, resp-map ← 01a, chains ← 01b
  itself); `requires` keeps it skipping earlier. Contract lockstep edits at
  01b (template + example): named in the Automated-checks block.
- **D budget.** `sync_information.py --d-budget N` (default 5, `0` disables):
  a feature whose D total exceeds the budget gets an advisory finding that
  names the budget and the reads — every D is a place a concept could decide
  instead; raising the budget is a recorded-reason decision at review time,
  not a silent threshold. Still always exit 0.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No runtime or derived-schema change. |
| Action ordering and sync deduplication | `preserved` | Stage-03 checks unchanged; 01b gains one advisory entry. |
| Flow-token lineage | `preserved` | Untouched. |
| Storage/retention semantics | `n/a` | No storage surface. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | Stage 01b + 03a contracts (template + example), `QUALITY_GATE.md`, `SYNC_PATTERNS.md` budget note, `CITATIONS.md` unchanged. |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | no | quality-gate scripts only. |
| Profile tests | yes | `tests/test_generate_review_views.py`, extensions to `tests/test_fr_dp_matrix.py` + `tests/test_sync_information.py`. |
| UC artefact chain | yes (derived views only) | Two new canonical 03a outputs — generated, manifest-listed, drift-checked; no judgement content. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Generator reproduces the worked example's committed views | unit | `tests/test_generate_review_views.py` | pass | `--check` PASS on UC-00 (3 fresh processes); both files committed to the example 03a output |
| Drift blocks: a mutated view fails `--check` | unit | `tests/test_generate_review_views.py` | pass | a hand edit fails `--check` (exit 1) with the regenerate hint |
| Manifest lists both views at 03a | gate | suite (`_manifest_check` wiring) + `expected_stage_outputs` | pass | 03a expected list gains `sync-information-profile.md` beside the existing `concept-matrix.md`; the worked example carries both |
| Matrix check also wired at 01b (lockstep) | unit + suite | `tests/test_fr_dp_matrix.py` + consistency suite | pass | 01b carries `fr_dp_matrix` (INDEX now reads "stage 01b; stage 03"); template + example 01b contracts name it |
| D-budget finding fires past the budget; exit 0 | unit | `tests/test_sync_information.py` | pass | 6 D reads → finding (6 > 5); `--d-budget 6` and `--d-budget 0` both silence; exit 0 always |
| Whole gate suite green | gate | `pytest quality-gate/tests`, `verify_artefacts.py` | pass | 377 passed (368→377); artefact gate intact; INDEX `--check` PASS |

## Gates

### Design gate

Approved in-conversation (2026-10-06): canonical manifest-listed 03a outputs
(the `pattern-d-summary` precedent) rather than optional/non-canonical; drift
blocks on staleness (the `shared_triggers_current` pattern); the matrix check
runs at 01b as well as 03; the D budget defaults to 5, is advisory, and is
overridable per run — not per repo (no new config key).

### Evidence gate

Approved — matrix above: 377 passed (368→377), --check PASS on the
worked example across 3 fresh processes, drift blocks on a hand edit,
manifest lists both views, 01b wiring lockstep green, D-budget finding
fires past the default and silences with --d-budget; artefact gate intact;
INDEX --check PASS.

- **Defect caught by the drift check itself:** `verify_concept_matrix.py` was nondeterministic across processes — `extract_concepts` returned a hash-ordered `set` and `detect_god_objects` iterated a hash-ordered dict, so with `PYTHONHASHSEED` randomization two subprocesses rendered different bytes and `--write` then `--check` disagreed. Fixed (sorted list + sorted iteration); proven stable across 3 fresh processes.

## Notes

- The views carry judgement-shaped *findings* (warnings) but are fully
  derived — the matrix cells, counts, and findings are deterministic from
  Gate-1 artifacts; nothing in them is authored.
- The two 01b-wired checks (novelty, this) plus the 03-wired set make the
  matrix run twice per feature — both advisory, both skip-cleanly before
  their inputs exist.
- Rollback: remove the check from 01b's list, the two Outputs entries, and
  the generator/verifier; the manifest derivation follows the contracts.
