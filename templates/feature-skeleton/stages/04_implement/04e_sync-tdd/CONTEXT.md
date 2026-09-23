# Stage 04e — Sync TDD (router)

## Pre-condition

`advance.py` enforces stage order and upstream gate approval before this
stage runs — see `STAGES.md` §"Stage lifecycle (standard)". Do not start
until it has printed this stage as `NEXT STAGE`.

## Why this stage exists

This stage is the ICM router for sync TDD. It exists to make the London
School red/green handoff structural: `04e-red` derives and approves
sync tests, `04e-green` implements only against those approved tests and
turns the outer flow tests green.

**Feeds:**

- approved red sync tests + handoff bundle -> `04e_green-impl/`
- green sync implementation and green flow tests -> `05_verify/`

**Agent stance for this stage:**
- If a sync needs imperative branching to make a test pass, the defect
  is in Stage 03; push the branching down into concept outcomes and
  re-derive the sync.
- `04e-red` may write sync tests and derivation artefacts only.
- `04e-green` may implement only against approved `04e-red` tests.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../03_syncs/output/` | 4 | Sync specs |
| `../04b_contract/output/` | 4 | Contract slices for the actions involved |
| `../04c_flow-tests/output/` | 4 | Outer flow expectations that must go green at the end |
| `../../../../../methodology/core/ITERATIVE_CHANGES.md` | 3 | Re-entry workflow for post-green sync changes |
| `../../../_config/build-and-test.md` | 3 | Canonical build/test command inherited by child stages |
| `../../../_config/package-and-layout.md` | 3 | Canonical package/source-root settings inherited by child stages |
| `../../../../../methodology/implementation/TDD.md` | 3 | London School structural handoff rules |

## Process

The child stages are executable auto-advance stages. Run them strictly in order:

1. [`04e_red-tests/`](04e_red-tests/CONTEXT.md) — derive executable
   sync tests, run them red, and record the handoff bundle.
2. [`04e_green-impl/`](04e_green-impl/CONTEXT.md) — implement only
   against the completed red sync tests until they and the `04c` flow
   tests are green.


## Progress checklist

- [ ] Red tests derived from Stage 03 sync specs
- [ ] Green implementation makes all sync tests pass
- [ ] Outer flow tests from 04c go green
- [ ] No imperative branching in sync classes (R3)
- [ ] Infrastructure controllers are transport-only (R4)
- [ ] Self-audit: `./clad verify` passes
## Outputs

(none — child stages own outputs and side effects)

## Verify

- `04e_red-tests/` was complete before `04e_green-impl/` started.
- Iterative-change readiness passes before sync implementation work starts.
- `04e_red-tests/output/sync-test-derivation.md` exists.
- All approved sync tests are green at the end of `04e_green-impl/`.
- All flow tests from `04c` are green at the end of `04e_green-impl/`.
- No extra executable syncs exist without an approved Stage 03 sync.

## Gate

Auto-advances through `04e-red`, `04e-green`, then Stage 05. Sync tests are
mechanically derived from approved chain tables and sync specs. The Stage 04e
implementation-parity and declarative checks (`verify_implementation_parity.py`,
`verify_sync_implementation_parity.py`, `verify_sync_declarative.py`,
`verify_sync_route_filters.py`, `verify_action_log_isolation.py`,
`verify_cucumber_green.py`) are the automated gate. No human approval is
required at the 04e-red boundary. The flow tests from 04c must go green at
the end of 04e-green.

## Advancing

> Do not open the next stage's `CONTEXT.md` yourself. After this stage's
> `output/` is written, end your turn by running the gate-driven advance
> command, which runs this stage's checks, enforces stage ordering, and
> tells you the next step:
>
> ```
> ./clad advance
> ```
>
> (Long form: `python3 quality-gate/advance.py --feature features/UC-XX-<slug>`.)
> The CLI wrapper auto-discovers the feature from `RESUME.md`.
>
> Treat its output as your next instruction. It advances you, stops you
> at a human gate, or returns you to this stage with the defects to fix.
> See AGENTS.md §2 principle 12 and
> `methodology/implementation/STAGES.md` §"Gate-driven advance".
