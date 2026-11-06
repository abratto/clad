# Maintenance change — `sync-gate-soundness`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `all profiles`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Close five false greens in the Stage-03/04e sync gates so a malformed rule, an unrelated carrier, a slice-only parity check, uncross-referenced matrix rows, or a mislabelled advisory check cannot pass.
- **Dependent re-entry:** `none`

## Why

An independent review reproduced five false greens by mutating temporary copies:
Stage 03 accepted an unparseable `when`/`then` body; transition coverage accepted
an unrelated `.sync.md` because counts matched; "strict" implementation parity
compared only the primary trigger and first target; the matrix did not
cross-reference row IDs against the chain table (`--chain-dir` was unused); and
the route-filter check was advisory while the index labelled it a gate.

## Mechanism

- **Rule well-formedness.** `artifact_parsers.sync_spec_problems` reports an
  empty trigger / empty conjunct / no target; `verify_sync_matrix.py` fails on it
  so an unparseable rule cannot become "nothing to analyse"
  (`verify_sync_matrix.py:check_sync_matrix`).
- **Exact transition coverage.** `verify_sync_transition_coverage.py` requires
  every derived stem for an active feature; the count-fallback is kept only for a
  frozen feature (Gate 3 approved), never as a substitute for a missing stem.
- **Full implementation parity.** `verify_sync_implementation_parity.py` compares
  every conjunct, every `then` target, the route literal, and the per-target
  argument names; an unextractable (helper-based) target is *unresolved* and
  fails under `--strict-trigger` instead of passing (`:body`).
- **Matrix cross-reference.** `verify_sync_matrix.py` parses columns by name,
  checks every row, and — with `--chain-dir` — requires each row ID to exist and
  each signature to name the referenced chain row's `then` action.
- **Label alignment.** `clad_stages.Check` gains an `advisory` flag; the
  route-filter check sets it, and `generate_gate_index.py` labels it "advisory"
  (matching its exit-0 behaviour).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No contract change |
| Action ordering and sync deduplication | `preserved` | Checks only; no runtime change |
| Flow-token lineage | `preserved` | Unchanged |
| Storage/retention semantics | `preserved` | Unchanged |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | no | — |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | no | — |
| Profile tests | yes | `quality-gate/tests/test_sync_gate_soundness.py` |
| UC artefact chain | no | Stage checks tightened; completed features are not re-checked |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| malformed rule fails Stage 03 | unit | `test_sync_gate_soundness.py::SyncMatrixSoundnessTests::test_malformed_rule_body_fails` | pass | suite green |
| bogus row IDs fail against chain | unit | `...::test_bogus_row_ids_fail_against_chain` | pass | suite green |
| signature must name chain action | unit | `...::test_signature_not_naming_chain_action_fails` | pass | suite green |
| missing transition + count-matching file fails (active) | unit | `TransitionCoverageSoundnessTests::test_missing_transition_with_count_matching_file_fails_when_active` | pass | suite green |
| frozen feature tolerates legacy naming | unit | `...::test_frozen_feature_tolerates_legacy_naming` | pass | suite green |
| second-conjunct route/action mismatch fails | unit | `ImplementationParitySoundnessTests::test_second_conjunct_route_mismatch_fails`, `...::test_second_conjunct_action_mismatch_fails` | pass | suite green |
| argument-name mismatch fails | unit | `...::test_argument_name_mismatch_fails` | pass | suite green |
| helper-based then is unresolved, not passed | unit | `...::test_helper_based_then_is_unresolved_not_passed` | pass | suite green |
| full gate | unit | `python3 -m pytest quality-gate/tests -q` | pass | 568 passed |

## Gates

Design and evidence gates approved; record closed.

## Notes

- Backward-compatible for completed features (per-stage checks run only for the
  active stage). The shipped `examples/UC-00-login` still passes the tightened
  matrix and parity checks.
- Rollback: revert the checkers; the DSL/engine is unchanged.
