# Maintenance change — `ad-design-deepening`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed` (`draft` until design approval, `active` while
  implementing, `closed` after evidence approval)
- **Affected profile(s):** all features (quality-gate scripts + the Stage 03
  stage contract in `templates/feature-skeleton`, mirrored in the worked
  example); no runtime profiles touched
- **Feature-contract impact:** `preserved` (advisory only — the FR×DP matrix
  never blocks; no derived-artefact or runtime contract changes)
- **Design gate:** `approved` (human, in-conversation: deepen the Axiomatic
  Design inventory along the three sketch items — citations + review stance,
  advisory Stage-03 wiring of the matrix (Stage 03 only), reviewability via
  `--output` + a `./clad matrix` wrapper, no stage artifact emission)
- **Evidence gate:** `approved`
- **Change summary:** Make Suh's Axiomatic Design an explicit, wired part of
  the workflow rather than script docstrings: cite Suh, teach the review
  stance in the Stage-03 contract (diagonal matrix = Independence Axiom), run
  `verify_concept_matrix.py` as an advisory Stage-03 check beside the
  blocking cycle graph and the advisory overlap check, and give reviewers a
  one-command surface (`./clad matrix`) plus a persisted matrix via
  `--output <path>` on request.

## Mechanism

- **Wiring** — `quality-gate/clad_stages.py` adds `_FR_DP_MATRIX` to
  `Stage("03")`: `--usecase <01_usecase/output/usecase.md>`, `--chain-dir
  <01b_chain-table/output>`, `--resp-map <01a_responsibility-map/output/…>`
  (requires all three; skips cleanly when they are absent, which at Stage 03
  never happens — the inputs are Gate-1 outputs). The script exits 0 by
  construction (advisory); no other stage wires it.
- **Lockstep (contract-consistency tests)** — the Stage-03 contract names
  `verify_concept_matrix.py` in its §"Automated checks" block and documents
  the anti-pattern semantics; gained `USECASE = _dir("01_usecase")` helper in
  `clad_stages.py`. The worked example's Stage-03 contract mirrors both.
- **Reviewability** — `./clad matrix` runs the script for the active feature
  (same azure auto-discovery as `./clad corpus-status`); `--output <path>`
  (pre-existing) persists the matrix as markdown on request. Pass lines
  carry no detail by design (`advance.py` prints details for skip/fail
  only), so the review surface is the human-run wrapper, not the
  `[pass]` line.
- **Citation** — `methodology/reference/CITATIONS.md` gains the Suh section
  (Axiomatic Design: Advances and Applications, 2001): scenarios = FRs,
  concepts = DPs, Independence Axiom = near-diagonal matrix.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No runtime or derived-schema change. |
| Action ordering and sync deduplication | `preserved` | Stage-03 checks extended with one advisory entry; blocking checks unchanged. |
| Flow-token lineage | `preserved` | Untouched. |
| Storage/retention semantics | `n/a` | No storage surface. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | Stage-03 contract (template + example), `QUALITY_GATE.md` §Axiomatic analysis, `CITATIONS.md`, `clad` help. |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | no | quality-gate scripts only. |
| Profile tests | yes | New `quality-gate/tests/test_fr_dp_matrix.py` (8 cases: builders + wiring + advisory-exit shape). |
| UC artefact chain | no | The matrix is a review instrument, not a stage output. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Matrix builders detect the three anti-patterns | unit | `tests/test_fr_dp_matrix.py` | pass | god object {Alpha} only @75%+, duplication = identical columns, entanglement pairs (incl. the semantically-correct rule that a God Object is maximally entangled); 8 cases |
| Wiring: Stage 03 carries `fr_dp_matrix`; args resolve to the feature's Gate-1 artifacts | unit | `tests/test_fr_dp_matrix.py` | pass | build_args point at `01_usecase/output/usecase.md` (caught+fixed: the wire initially passed the output *directory*); requires skip cleanly on a pristine root |
| Advisory by construction | unit | script body contains `exit(0` | pass | never blocks |
| Whole gate suite + artefact pipeline green | gate | `pytest quality-gate/tests`, `verify_artefacts.py` | pass | 362 passed (354→362); three consecutive clean full runs; artefact gate intact; INDEX.md regenerated deterministically (`--check` PASS); matrix advisory-run on the worked example produces the review surface; contract-consistency tests green in-suite (wiring ⇄ contract lockstep holds) |

## Gates

### Design gate

Approved in-conversation (2026-10-05): both recommendations adopted — the
matrix runs advisively **at Stage 03 only** (Gate-2 surface; 01b would add
advisory noise before concepts exist), and reviewability comes from
`--output` + the `./clad matrix` wrapper rather than a canonical stage
artifact (no manifest or gate-hash coupling without a consumer).

### Evidence gate

Approved — matrix above: 8 new unit cases (builders + wiring + advisory
shape), pytest 362 passed (three consecutive clean full runs), artefact gate
intact, INDEX.md deterministic-regeneration PASS, contract-consistency
lockstep green in-suite, advisory matrix run on the worked example.

## Notes

- The wiring follows the 0.19 advisory-check precedents
  (`concept_overlap_lint`, `plan_concept_order`): always exit 0, findings as
  warnings; blocking checks stay blocking.
- `verify_concept_matrix.py` needed no behaviour change — its `--output`
  already renders the matrix markdown; only the Stage-03 wire, the wrapper,
  the citations, and the reviewer prose are added.
- Deferred (gated decisions if demand shows): persisting
  `fr-dp-matrix.md` into 03(a) stage outputs; running the matrix against
  Gate-1 inputs (01b) as well.
- Rollback: remove `_FR_DP_MATRIX` from the Stage-03 checks list and the
  contract block; the wrapper and docs are inert without it.
