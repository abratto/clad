# Stage 04 — Implement (router)

This directory owns no artefacts or transition. It is a reference
container for three implementation sub-stages plus the Gate-3
acceptance stage.

> **Completed example.** The worked instance of the implementation stages is at
> [`../../../../examples/UC-00-login/stages/04_implement/`](../../../../examples/UC-00-login/stages/04_implement/) — read it if useful; it is illustrative, not a template.

## Why this stage exists

**Spec-driven, test-verified implementation.** Design was settled in
Stages 01–03 and frozen as contracts at 04b. Stage 04 executes it:

- `04c` authors the **Acceptance Spec** and the native flow tests
  (Gate 3 — the frozen acceptance spec).
- `04d` implements concepts and their unit tests.
- `04e` implements syncs and their unit tests; the acceptance tests go
  green here.

There is **no red/green sub-stage split** — tests are derived from
already-approved artefacts and produced alongside implementation. Test
effectiveness is measured by mutation score, not by process adherence
(see `methodology/implementation/TESTING.md`).

Stage 04 is the **executable implementation stage**. The markdown
derivation files produced in `04b`/`04c`/`04d`/`04e` are supporting
artefacts, not substitutes for code or tests. A Stage 04 sub-stage is
not complete unless its required side effects exist in the selected
profile and the required commands have been executed for that sub-stage.

**Feeds:**

- (this router owns no artefacts — sub-stages do.)
- the running, compilable artefact -> Stage 05 (back-trace target + smoke target).

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../03b_data-model/output/` | 4 | Approved conceptual data models |
| `../02_concepts/output/concept-bindings.md` | 4 | Which canonical concepts this feature uses |
| `../../../../features/_system/concepts/` | 4 | Canonical concept specs (`state`, actions) |
| `../02_concepts/output/<Name>.concept.md` | 4 | NEW/EXTEND proposals (not yet promoted) |
| `../03_syncs/output/` | 4 | Sync specs |
| `../../../../methodology/core/ITERATIVE_CHANGES.md` | 3 | Re-entry workflow for post-green changes |
| `../../../../templates/artefact-impact-matrix.md` | 3 | Required `_changes/` worksheet for iterative changes |
| `../../../../methodology/implementation/STAGES.md` | 3 | Stage 04 routing contract |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rules |
| `../../../../methodology/implementation/TESTING.md` | 3 | Spec-driven verification discipline |
| `../../../../reference-impl/java-legible/README.md` (default profile) | 3 | Runtime evidence surface for the canonical fire-after-commit profile |

## Process

Run the executable sub-stages **strictly in order**. Before
starting any sub-stage, verify its pre-condition is met. If it is not,
stop and tell the human which earlier sub-stage must be completed first.

| # | Sub-stage | Pre-condition before starting |
|---|---|---|
| 1 | [`04a_storage-mapping/`](04a_storage-mapping/CONTEXT.md) — optional profile mapping | `03b_data-model/output/` is non-empty |
| 2 | [`04b_contract/`](04b_contract/CONTEXT.md) — per-concept contract slice | `04a_storage-mapping/output/` exists (or `_NOT_APPLICABLE.md` present) |
| 3 | [`04c_acceptance-tests/`](04c_acceptance-tests/CONTEXT.md) — Acceptance Spec + native flow tests | `04b_contract/output/` is non-empty |
| 4 | [`04d_concept-impl/`](04d_concept-impl/CONTEXT.md) — concepts + unit tests | `04c_acceptance-tests/output/` is non-empty and Gate 3 is approved |
| 5 | [`04e_sync-impl/`](04e_sync-impl/CONTEXT.md) — syncs + unit tests | concept tests from `04d` are green |

During `04c` through `04e`, if the selected profile exposes a runtime
debug surface, use it as the default evidence source for explaining
live behaviour. For the Java reference profile, prefer `/api/dev/flows`
to inspect registered sync order, `/api/dev/flow/{token}` to inspect a
single archived flow, `/api/dev/stuck` to find active actions missing
`:output`, and `/api/dev/concept/{name}/triples` to inspect concept
state. Do not claim runtime traceability from predicted tokens, test
comments, or markdown derivations alone when a profile debug surface is
available.

For bootstrap / `Web` implementations, keep the transport boundary
strict: normalize input, invoke the flow root, await the authored
response, and translate transport output. Do not call business concept
classes directly, branch on domain outcomes, compute domain policy, or
read/mutate concept state in the controller/route handler.

**Do not skip or reorder sub-stages.** When in doubt, use
one-stage-per-turn.

## Outputs

(none — sub-stages own all artefacts)

## Verify

- Every executable sub-stage has recorded its required output evidence.
- For iterative changes, `quality-gate/verify_iterative_change_readiness.py`
  passes before 04d/04e work starts, and
  `quality-gate/verify_iterative_change_coupling.py` passes before merge.
- `04b` exists before any `04c`/`04d`/`04e` work.
- `04c` is complete and Gate 3 approved before `04d` starts.
- Concept tests are green before `04e` starts.
- No sub-stage is treated as complete from markdown outputs alone; each
  required code/test side effect exists for the selected profile.
- The acceptance tests authored at `04c` are green at the end of `04e`.
- Any runtime explanation of a flow being stuck or archived is backed by
  the profile's debug surface or an equivalent executed runtime
  inspection command.
- Any bootstrap / `Web` implementation is transport-only: no direct
  business-concept dependency, no domain branching, and no concept-state
  read/write in the controller/route handler.
- **Cross-stage check (back):** every concept and every sync from
  stages 02 and 03 has a corresponding sub-stage output.

## Gate

Auto-advances. **Sub-stage 04c (acceptance tests) is Gate 3 (Acceptance
spec) — the human reviews `usecase.md` + the frozen
`acceptance-spec.md`.** After 04c is approved, sub-stages 04d and 04e
auto-advance because their tests are mechanically derived from
already-approved artefacts (contracts, chain tables, sync specs). The
inner stages verify implementation fidelity; the design was settled at
04c.

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

> **In-memory profiles:** 04a is satisfied by a `_NOT_APPLICABLE.md` note in
> its `output/`; `advance.py` then routes you to 04b.
