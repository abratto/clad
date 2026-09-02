<!-- Maintenance-route planning record. -->
# Maintenance change — `workflow-control-two-dimensions`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `all profiles`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Replace the three-level `workflow.autonomy` knob (`gated`/`auto`/`yolo`) with two independent boolean knobs — `workflow.autonomous` (gate approval) and `workflow.session-per-stage` (context-window/session handoff).

## Why

Two related needs converge on this change:

1. **The single `workflow.autonomy` knob conflated two distinct concerns** —
   *who approves the 3 gates* versus *how much the agent stops*. The `yolo`
   level bundled a third, unrelated behaviour (downgrading failing checks to
   warnings) that has no principled place once the dimensions are separated.
2. **CLAD's session model was undocumented.** CLAD inherited ICM's folder
   shape but not its context-scoping economics: stages were run in one
   continuous session, with a fresh-session boundary available only as the
   `HANDOVER.md` recovery prompt. Operators who wanted "one session per
   stage, context cleared between stages" had no first-class way to ask for
   it.

The fix separates the two axes and makes the fresh-session boundary a named,
deterministic, human-only mode.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | No concept/sync/spec surface changes; this is process tooling only. |
| Action ordering and sync deduplication | preserved | Unchanged — `advance.py` transition logic only. |
| Flow-token lineage | preserved | Unchanged — no runtime surface touched. |
| Storage/retention semantics | preserved | Unchanged — no storage surface touched. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `methodology/ORIGINS.md` ("How CLAD diverges from ICM"), `methodology/implementation/STAGES.md` (§"Workflow control"), `methodology/implementation/HANDOVER.md`, `AGENTS.md` §2 rule 13 + §4a, `README.md` |
| Profile configuration or deployment files | yes | `clad.properties` — `workflow.autonomy=gated` removed; `workflow.autonomous` + `workflow.session-per-stage` added |
| Engine/runtime implementation | yes | `quality-gate/advance.py` — two booleans, `emit_handoff()` + exit `30`, no `yolo` downgrade, consolidated duplicated gate block |
| Profile tests | yes | `quality-gate/tests/test_stage_workflow.py` (existing suite must still pass — no test edits expected) |
| UC artefact chain | no | Feature stage artefacts and receipts are unchanged; only the workflow-control surface changes. Existing `.gate-receipt.json` files carry the old `autonomy` key — treated as historical, no re-entry required. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| advance.py compiles under both knobs | unit | `python3 -m py_compile quality-gate/advance.py quality-gate/clad_stages.py` | pass | exit 0 |
| Existing stage-routing regressions unaffected | unit | `python3 -m unittest quality-gate.tests.test_stage_workflow` | pass | 13/13 OK |
| All four knob combinations behave correctly | smoke | `advance.py` on scratch feature copies: `false/false`→exit 0, `false/true`→exit 30 (slug substituted), `true/false`→auto-approve+continue, `true/true`→auto-approve+exit 30 with bypassed-review warning | pass | exit codes 0/30 observed; `auto-approved` ledgered; 0 leftover `{{UC-XX-slug}}` placeholders |

## Gates

### Design gate

The human reviews contract impact, non-goals, and the test matrix before a
maintenance-scoped implementation or deployment file changes. Approve with
`./clad approve-maintenance workflow-control-two-dimensions design`, then set Status to `active`.

### Evidence gate

The human reviews the completed test matrix and runtime evidence before commit.
After approval, set Status to `closed` and commit the record with the change.

## Notes

- **Migration of existing receipts:** historical `.gate-receipt.json` files
  still contain the `autonomy` key (e.g. `"autonomy": "gated"`). These are
  read-only historical records; `verify_artefacts.py` does not require
  rewriting them, and no re-entry is needed because the feature contract is
  unchanged.
- **`yolo` retirement is intentional:** the "downgrade failing checks to
  warnings" behaviour is removed. Failing deterministic checks now block
  under every combination. A skipped-stage gap always hard-blocks, as before.
- **`clad-agent` staleness:** the `clad-agent` repo bundles a frozen
  `methodology/` snapshot under `src/main/resources/clad/knowledge/`. Its
  `CladCompatibilityChecker` may flag the removed `yolo` level. A separate
  decision (version-pin vs live-read vs manual sync) is needed — tracked
  outside this record.
