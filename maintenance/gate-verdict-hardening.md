# Maintenance change — `gate-verdict-hardening`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md` §"Platform maintenance changes" and R20
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `quality-gate` scripts (no engine/profile/runtime change)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Fix three false-green (silent-pass) gate conditions, centralise the RESUME gate-line grammar, make a silent gate-write failure loud, and normalise the shared-triggers staleness comparison. Each fix is test-first: the failure mode had no regression test, which is why it survived.

## Why

A gate that exits 0 when it should fail undermines the "deterministic checks
block" guarantee. Four scripts treat missing, empty, or malformed input as
success instead of skip-or-fail. Each was reproduced against the source.

### Item 1 — false greens (silent pass on a defect)

1. **`verify_outcome_alignment.py`.** When every chain row is a terminal respond
   row, `parse_chain_outcomes` filters them all out, `chain_rows` is empty, and
   the script prints `WARN no chain rows found` and exits 0. A populated chain
   directory that yields zero comparable rows is a **defect** (a chain table with
   no sync-trigger rows), not an absence. Today it passes silently.
2. **`verify_scenario_coverage.py`.** When `--chain-dir` does not exist,
   `chain_files` becomes `[]` and the `and chain_files` guards on checks 2 and 3
   silently skip them — exit 0. A missing chain directory *when scenarios exist*
   must not pass: every scenario is then unverified.
3. **`verify_concept_additivity.py`.** `dropped_contract_terms` returns `[]`
   (pass) when the proposal's `04b_contract` directory has no outcomes for a
   concept whose canonical contract has some (`if not before or not after:
   return []`). A dropped canonical contract (the proposal simply never derived
   it) goes undetected.

This class is not theoretical: the `verify_artefacts.py` FAIL observed during the
`engine-record-collect` work (`require exactly one active maintenance record` on
a mid-transition tree) is the same missing-input-as-nonfatal shape.

### Item 2 — three copies of the RESUME gate-line grammar

The gate-status pattern is hardcoded in three places that must agree but do not:

| Site | Regex | Read/Write | Adornment tolerance |
|---|---|---|---|
| `verify_stage_sequence.py:157` (`gate_status`) | `^- \*\*Gate N \(Label\):\*\*\s+\`([\w-]+)\`` | read | none |
| `verify_concept_registry.py:37` (`GATE2_APPROVED`) | `^- \*\*Gate 2 \([^)]*\):\*\*\s+\`approved\`` | read | none, label-agnostic |
| `advance.py:109` (`set_gate_status`) | `(- \*\*Gate N \(Label\):\*\*)\s+\`[\w-]+\`.*` | read/write | none |

Three copies of one grammar is a drift source; the write side is the strictest
and silently no-ops on any variation.

### Item 3 — silent gate-write failure

`advance.py:set_gate_status` returns `False` with no warning when its pattern
matches nothing (e.g. a RESUME whose gate line is malformed). The approval is
then never recorded and the feature reads `pending` forever — a permanent,
invisible blocker.

### Item 5 — shared-triggers staleness from formatting

`verify_shared_triggers_current.py:44` compares `current.strip() !=
fresh.strip()`, so a benign generator formatting change (trailing whitespace,
line endings) reports false staleness. Only *logical* change should register.

## Rule

- **Item 1 (each).** Distinguish **absence** from **defect**:
  - input absent (directory/file does not exist) → `SKIP` (exit 0), explicitly
    logged, and only where absence is genuinely legal;
  - input present but parses to no comparable content while content was expected
    → `FAIL` (exit 1).
- **Item 2.** One parse/write helper pair in `artifact_parsers.py` (the
  artefact-grammar single source of truth): e.g.
  `parse_gate_status(text, gate, label) -> str | None` and
  `set_gate_status(text, gate, label, status) -> (text, bool)`. All three callers
  import from it; no caller re-states the pattern.
- **Item 3.** `set_gate_status` (via the shared writer) prints a `WARN` naming
  the feature, the gate, and the expected line format when nothing matches.
- **Item 5.** Compare on normalised content (collapse `\r\n`→`\n`, strip trailing
  whitespace per line) — logical comparison, not byte equality.

## Mechanism

The verdict changes are local to the checks: `verify_outcome_alignment.py`'s
`if not chain_rows:` branch now asks `_chain_row_files`
(quality-gate/verify_outcome_alignment.py:52) whether any chain file exists at
all before deciding skip vs fail; `verify_scenario_coverage.py` decides on
`os.path.isdir(args.chain_dir)` with scenarios present
(quality-gate/verify_scenario_coverage.py:55); `verify_concept_additivity.py`
returns the `<entire contract missing>` marker when a canonical contract has no
proposal counterpart (quality-gate/verify_concept_additivity.py:100). The shared
gate-line grammar is `artifact_parsers.parse_gate_status`/`set_gate_status`
(quality-gate/artifact_parsers.py:1280), called by
`verify_stage_sequence.gate_status`, `verify_concept_registry.gate2_approved`,
and `advance.set_gate_status`.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Gate scripts only; no artefact or runtime change |
| Action ordering and sync deduplication | `preserved` | — |
| Flow-token lineage | `preserved` | — |
| Storage/retention semantics | `preserved` | — |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | no | — |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | no | — |
| Gate scripts | yes | `verify_outcome_alignment.py`, `verify_scenario_coverage.py`, `verify_concept_additivity.py`, `verify_shared_triggers_current.py`, `verify_stage_sequence.py`, `verify_concept_registry.py`, `advance.py`, `artifact_parsers.py` |
| Profile tests | no | — |
| Gate tests | yes | new regression tests for each fix; a shared gate-line parser test |
| UC artefact chain | no | UC-00 must still pass on the current green tree |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Outcome alignment FAILs on a present chain dir that parses to zero rows | unit | `test_gap_checks.py::…test_outcome_alignment_fails_on_empty_chain_rows` | pass | — |
| Outcome alignment still SKIPs when the chain dir is absent | unit | `test_gap_checks.py::…test_outcome_alignment_skips_when_chain_dir_absent` | pass | — |
| Scenario coverage FAILs when the chain dir is missing but scenarios exist | unit | `test_gap_checks.py::…test_scenario_coverage_fails_on_missing_chain_dir_with_scenarios` | pass | — |
| Concept additivity FAILs when a canonical contract has no proposal counterpart | unit | `test_gap_checks.py::…test_additivity_fails_on_missing_proposal_contract`, `test_concept_additivity.py::…test_missing_proposal_contract_fails` | pass | — |
| Gate-line parse/write round-trips both skeleton and UC-00 formats | unit | `test_parser_regressions.py::GateLineParsingTests` (6 cases) | pass | — |
| `set_gate_status` WARNs when no gate line matches (and on a missing RESUME) | unit | `test_stage_workflow.py::…test_set_gate_status_warns_when_no_gate_line_matches`, `…warns_when_resume_missing` | pass | — |
| Shared-triggers treats whitespace/EOL-only change as current | unit | `test_gap_checks.py::…test_shared_triggers_ignores_whitespace_drift` | pass | — |
| UC-00 still passes the corrected scripts on the green tree | integration | `verify_outcome_alignment` (8 outcomes), `verify_concept_additivity` (SKIP), `verify_shared_triggers_current` (PASS) against `features/UC-00-login` | pass | — |
| Gate pipeline intact | integration | `python3 quality-gate/verify_artefacts.py` | pass | artefact pipeline intact, 0 WARNs |
| Gate suite green | unit | `python3 -m pytest quality-gate/tests -q` | pass | 246 passed |

## Gates

### Design gate

To be approved before implementation (changes gate verdicts). Approve with
`./clad approve-maintenance gate-verdict-hardening design`.

### Evidence gate

Cleared: each new regression test reproduces its false-green/staleness before the fix and passes after; the two fixtures that had relied on the old additivity skip were corrected to isolate the state-line concern. UC-00 still passes every corrected script; the artefact pipeline is intact (0 WARNs) and the gate suite is green at 246.

## Notes

- **Open question for the human (not an action).** The always-advisory checks
  (`verify_concept_matrix`, `verify_code_refs`, `verify_governance_hygiene`) each
  exit 0 unconditionally. On reference-count grounds no script is a safe removal.
  The only question is *policy*: should any be demoted from a gate to advisory
  tooling, or promoted to blocking? This record does not change them; it raises
  the question so the decision is explicit.
- The fixes are conservative on absence: a genuinely missing input (e.g. a
  feature that has no chain directory yet) still skips, so the corrections do not
  break features mid-pipeline.
