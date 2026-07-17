# Stage 04 — Implement (router)

This stage owns no artefacts of its own. It routes to five top-level
sub-stages; `04d` and `04e` are themselves routers with structural
red/green child stages.

## Why this stage exists

**Outside-in TDD double-loop.** The outer loop is one failing flow
test per use-case scenario (`04c`). The inner loop is per-concept
(`04d-red` -> `04d-green`) and per-sync (`04e-red` -> `04e-green`).
`04a` and `04b` prepare the ground (profile mapping and per-concept
SPEC slice). Order matters: profile mapping before tests when a
persistent store exists, tests before code, concept code before sync
code, sync code is what turns the outer flow test green.

Stage 04 is the **executable implementation stage**. The markdown
derivation files produced in `04b`/`04c`/`04d-red`/`04e-red` are
supporting artefacts, not substitutes for code or tests. A Stage 04
sub-stage is not complete unless its required side effects exist in the
selected profile and the required commands have been executed for that
sub-stage.

**Feeds:**

- (this router owns no artefacts — sub-stages do.)
- the running, compilable artefact -> Stage 05 (back-trace target + smoke target).

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../03b_data-model/output/` | 4 | Approved conceptual data models |
| `../02_concepts/output/` | 4 | Concept specs |
| `../03_syncs/output/` | 4 | Sync specs |
| `../../../../methodology/core/ITERATIVE_CHANGES.md` | 3 | Re-entry workflow for post-green changes |
| `../../../../templates/artefact-impact-matrix.md` | 3 | Required `_changes/` worksheet for iterative changes |
| `../../../../methodology/implementation/STAGES.md` | 3 | Stage 04 routing contract |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rules |
| `../../../../reference-impl/java-micronaut-jena/README.md` | 3 | Example runtime debug surface for the Java profile |

## Process

Run the sub-stages **strictly in order**, gating after each. Before
starting any sub-stage, verify its pre-condition is met. If it is not,
stop and tell the human which earlier sub-stage must be completed first.

| # | Sub-stage | Pre-condition before starting |
|---|---|---|
| 1 | [`04a_storage-mapping/`](04a_storage-mapping/CONTEXT.md) — optional profile mapping | `03b_data-model/output/` is non-empty |
| 2 | [`04b_spec/`](04b_spec/CONTEXT.md) — per-concept SPEC slice | `04a_storage-mapping/output/` exists (or `_NOT_APPLICABLE.md` present) |
| 3 | [`04c_flow-tests/`](04c_flow-tests/CONTEXT.md) — outer red (flow tests) | `04b_spec/output/` is non-empty |
| 4 | [`04d_concept-tdd/`](04d_concept-tdd/CONTEXT.md) — router for `04d_red-tests/` then `04d_green-impl/` | `04c_flow-tests/output/` is non-empty |
| 5 | [`04e_sync-tdd/`](04e_sync-tdd/CONTEXT.md) — router for `04e_red-tests/` then `04e_green-impl/` | All concept tests from `04d_green` are green |

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

**Do not skip or reorder sub-stages.** The fast-path exception in
`STAGES.md` applies only when all listed conditions hold; when in
doubt, use one-stage-per-turn.

## Outputs

(none — sub-stages own all artefacts)

## Verify

- Every sub-stage has been gated.
- For iterative changes, `quality-gate/verify_iterative_change_readiness.py`
  passes before 04d/04e work starts, and
  `quality-gate/verify_iterative_change_coupling.py` passes before merge.
- `04b` exists before any `04c`/`04d`/`04e` work.
- `04d_red-tests/` is approved before `04d_green-impl/` starts.
- `04e_red-tests/` is approved before `04e_green-impl/` starts.
- No sub-stage is treated as complete from markdown outputs alone; each
  required code/test side effect exists for the selected profile.
- The flow tests from `04c` are green at the end of `04e_green`.
- Any runtime explanation of why a flow is red, green, stuck, or
  archived is backed by the profile's debug surface or an equivalent
  executed runtime inspection command.
- Any bootstrap / `Web` implementation is transport-only: no direct
  business-concept dependency, no domain branching, and no concept-state
  read/write in the controller/route handler.
- **Cross-stage check (back):** every concept and every sync from
  stages 02 and 03 has a corresponding sub-stage output.

## Gate

Auto-advances (next human gate: Stage 04c). Sub-stages 04a and 04b auto-advance.
**Sub-stage 04c (flow tests) is Gate 3 (Executable specification) —
human reviews the Gherkin `.feature` files as the executable form of
the use case.** After 04c is approved, sub-
stages 04d and 04e auto-advance because their tests are mechanically
derived from already-approved artefacts (SPECs, chain tables, sync
specs). The inner loops verify implementation fidelity; the design
was settled at 04c.

## Next stage

-> [`04a_storage-mapping/CONTEXT.md`](04a_storage-mapping/CONTEXT.md) — Storage mapping

For in-memory profiles, skip 04a and go straight to
[`04b_spec/CONTEXT.md`](04b_spec/CONTEXT.md). Mark 04a with a
`_NOT_APPLICABLE.md` note in its `output/`.

The agent proceeds without a human gate.
