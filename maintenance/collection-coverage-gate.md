# Maintenance change — `collection-coverage-gate`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** all profiles (gate + stage contract + Gherkin template/methodology)
- **Feature-contract impact:** `preserved` (additive design-time gate; no artefact shape or outcome changes)
- **Design gate:** `approved` (human in-conversation: adopted the gap-closing plan)
- **Evidence gate:** `approved` (test matrix below)
- **Change summary:** Add `quality-gate/verify_collection_coverage.py`, wired into Stage 04c, requiring a **`## Collection coverage`** declaration (empty / multi-item / repeated-key) whenever a feature's chain tables or SPECs expose a collection response. Forward-only: a feature already closed at Stage 05 is skipped (no retrofit).

## Why (experiment-found)

The 13-use-case Conduit rebuild surfaced twice that **design-time gates verify structure, not cardinality**:

- **UC-07 (view comments):** the empty thread (a `fanOut` over zero comments → zero frames → the join never fired) and a multi-comment thread (a `collectBy` that gathered only one completion) passed every gate and were caught only by Stage-05 runtime back-trace.
- **UC-12 (view feed):** a page with a **repeated author** misaligned the per-article `following` flags — again invisible to every gate, caught at Stage 05.

Both are the same shape: a collection fixture the flow tests did not exercise. `AGENTS.md`-adjacent analysis in the experiment recommended a required empty-collection + multi-item fixture at Stage 04c; this change implements it.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No artefact shape/outcome change; gate is additive |
| Action ordering and sync deduplication | `preserved` | — |
| Flow-token lineage | `preserved` | — |
| Storage/retention semantics | `preserved` | — |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine/runtime implementation | no | — |
| Gate scripts | yes | new `quality-gate/verify_collection_coverage.py`; registered on Stage 04c in `clad_stages.py` |
| Gate tests | yes | new `quality-gate/tests/test_collection_coverage.py` (7 cases) |
| Stage contract | yes | `templates/feature-skeleton/stages/04_implement/04c_flow-tests/CONTEXT.md` — Process step 8, Outputs, Verify, checklist |
| Gherkin docs/templates | yes | `templates/feature.feature` rider; `methodology/architecture/GHERKIN_INTEGRATION.md` Rule G6 + Stage-04c verify + agent checklist |
| UC artefact chain | no (forward-only) | Closed features (Stage-05 trace present) are skipped |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Non-collection feature skips | unit | `pytest quality-gate/tests/test_collection_coverage.py` | pass | 1 case |
| Closed collection feature skips (no retrofit) | unit | same | pass | 1 case |
| Declared coverage passes | unit | same | pass | 1 case |
| Missing section fails; missing entry fails | unit | same | pass | 2 cases |
| `--advisory` downgrades a failure | unit | same | pass | 1 case |
| `List<...>` SPEC is collection-shaped | unit | same | pass | 1 case |
| Wired check named in the stage contract | unit | `pytest quality-gate/tests/test_stage_contract_consistency.py` | pass | — |
| Gate suite + pipeline intact | unit/integration | `pytest quality-gate/tests -q`; `python3 quality-gate/verify_artefacts.py` | pass | 116 tests; pipeline intact |

## Gates

### Design gate

Approved in-conversation (the human adopted the post-experiment gap-closing plan; scope explicitly excludes the transport adapter and HURL tier).

### Evidence gate

Recorded from the executed gate suite and `verify_artefacts.py`; Status `closed` with the change commit. The 13 rebuild features are grandfathered (Stage-05 trace present) so the fork's pipeline stays green on inheritance.

## Notes

- Downstream: the conduit rebuild fork inherits the script, tests, `clad_stages.py` wiring, the skeleton 04c contract, the feature template, and the Gherkin methodology verbatim. Its closed features skip; new features are enforced.
