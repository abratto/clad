# Stages — how the CLAD loop maps onto the ICM scaffold

## Scope: system-level vs per-UC

Not all stages operate at the same scope. This distinction matters
before you open any `CONTEXT.md`:

| Scope | Stage | Folder | Created when |
|---|---|---|---|
| **System-level** (once per project brief) | 00 | `features/_system/stages/00_actor-goal/` | Exists in the repo; use as-is |
| **Per-UC** (once per in-scope goal) | 01–05 | `features/UC-XX-<slug>/stages/NN_*/` | Created after Stage 00 gate, one folder per confirmed in-scope goal |

**The order is non-negotiable:**

1. Run Stage 00 inside `features/_system/` against your project brief.
   Stage 00 is multi-turn; write nothing until the human approves.
2. Read the confirmed `goals.md`. Count the in-scope goals.
3. Copy `templates/feature-skeleton/` to a new `features/UC-XX-<slug>/`
   folder for **each** in-scope goal (UC numbers from 01).
4. Run Stages 01–05 inside each UC folder, one goal at a time.

`features/_system/` never grows beyond Stage 00 output. Every stage
from 01 onwards lives inside a per-UC folder.

---

CLAD's contract loop has six steps once the outside-in TDD discipline
is unfolded:

```
actor/goal -> use case -> concepts -> syncs -> implement -> verify
                                              (04a..04e)
```

Each step is one ICM stage. Stage 04 (implement) decomposes further
into five sub-stages that capture the **outside-in TDD double-loop**:
the outer loop is a flow test (red), the inner loop is per-concept and
per-sync TDD (red → green).

## Folder layout

```
features/UC-XX-name/
├── README.md
├── _config/                     Feature-scoped reference (Layer 3)
└── stages/
    ├── 01_usecase/
    │   ├── CONTEXT.md
    │   └── output/              usecase.md
    ├── 02a_responsibility-map/
    │   ├── CONTEXT.md
    │   └── output/              responsibility-map.md
    ├── 02b_chain-table/
    │   ├── CONTEXT.md
    │   └── output/              <scenario>-chain.md (one per use-case scenario)
    ├── 02_concepts/
    │   ├── CONTEXT.md
    │   └── output/              <Name>.concept.md (one per concept)
    ├── 03_syncs/
    │   ├── CONTEXT.md
    │   └── output/              <name>.sync.md (one per rule)
    ├── 03a_dependency-review/
    │   ├── CONTEXT.md
    │   └── output/              <concept>-card.md per concept; pattern-d-summary.md
   ├── 03b_data-model/
   │   ├── CONTEXT.md
   │   └── output/              <Name>.data-model.md per concept
    ├── 04_implement/
    │   ├── CONTEXT.md           Router → 04a..04e; no direct artefacts
   │   ├── 04a_storage-mapping/ Optional profile mapping
    │   │   ├── CONTEXT.md
    │   │   └── output/
    │   ├── 04b_spec/            Per-concept SPEC contract slice
    │   │   ├── CONTEXT.md
    │   │   └── output/          <Name>.spec.md
    │   ├── 04c_flow-tests/      Outside-loop red: HTTP → flow-token tree
    │   │   ├── CONTEXT.md
    │   │   └── output/
   │   ├── 04d_concept-tdd/     Router: concept red/green split
   │   │   ├── CONTEXT.md
   │   │   ├── 04d_red-tests/
   │   │   │   ├── CONTEXT.md
   │   │   │   └── output/      concept-test-derivation.md
   │   │   └── 04d_green-impl/
   │   │       └── CONTEXT.md
   │   └── 04e_sync-tdd/        Router: sync red/green split
   │       ├── CONTEXT.md
   │       ├── 04e_red-tests/
   │       │   ├── CONTEXT.md
   │       │   └── output/      sync-test-derivation.md
   │       └── 04e_green-impl/
   │           └── CONTEXT.md
    └── 05_verify/
        ├── CONTEXT.md
        └── output/              trace.md, findings.md, smoke.md, tracking.md
```

## Gate model

Per-UC stages are grouped into **3 human gates**, each answering one
design question. Between gates, stages auto-advance: the agent runs
the quality-gate scripts as a self-audit and proceeds without human
intervention. If any quality-gate check fails, the agent stops and
surfaces the defect.

Rejection at any gate sends work back to the earliest stage that owns
the defect. The agent does not advance past the gate until the human
approves.

## Gate-driven advance

The agent does not self-select the next stage. Choosing the next step is
where a model most often skips a stage or its verification, so that
decision is owned by a deterministic script rather than the model.

After a per-UC stage's `output/` is written, the agent ends its turn by
running:

```
python3 quality-gate/advance.py --feature features/UC-XX-<slug>
```

`advance.py` is a thin composition over the existing pieces — it does not
re-implement any check:

1. **Sequence / entry guard.** It runs
   [`../../quality-gate/verify_stage_sequence.py`](../../quality-gate/verify_stage_sequence.py),
   which fails if any earlier stage's `output/` is empty (a skipped
   stage) or if a human gate that precedes the current stage is not
   `approved` in `RESUME.md`.
2. **Stage checks.** It runs the `quality-gate/verify_*.py` scripts
   mapped to that stage (the same scripts listed in
   [`QUALITY_GATE.md`](QUALITY_GATE.md)). A check whose inputs do not
   exist yet is reported as `skip`, not a failure.
3. **Receipt.** It writes a `.gate-receipt.json` into the stage's
   `output/` recording which checks ran, their exit codes, a content
   hash of the outputs, and the overall result. `verify_stage_sequence.py
   --require-receipts` can later confirm no stage was edited after its
   checks last passed (stale-receipt detection).
4. **Next instruction.** Based on the outcome it prints exactly one of:
   - **PASS, no gate** → the next stage's `CONTEXT.md` path and a ready
     prompt (and updates the `RESUME.md` pointer). Exit `0`.
   - **PASS, human gate** → the artefact summary (via `present_gate.py`)
     and the approval commands. Exit `10`. The agent presents the
     summary and waits; after the human approves and `approve_gate.py`
     records it, re-running `advance.py` crosses the gate.
   - **FAIL** → the specific defects and a correction prompt scoped to
     the current stage. Exit `1`. The agent must not advance.

The stage model that `advance.py` and `verify_stage_sequence.py` share
lives in [`../../quality-gate/clad_stages.py`](../../quality-gate/clad_stages.py)
— the single source of truth for stage order, gate placement, and the
stage→checks map.

This is a local, per-stage gate: a defect is caught the moment the stage
finishes, before later stages build on top of it — not at commit time.
The pre-commit/CI gate in [`DELIVERY.md`](DELIVERY.md) remains the
downstream backstop for anyone who bypasses the local loop; wiring the
same scripts into a CI profile is encouraged but optional and is not
shipped enabled in this template.

Stage 00 (system scope) is exempt: it is the collaborative intake stage
and runs before the per-UC advance loop exists.

### Autonomy override (opt-in, human-only)

Some operators want the agent to run the pipeline with less stopping.
`advance.py` reads a `workflow.autonomy` setting (from `clad.properties`,
the `CLAD_AUTONOMY` env var, or a `--autonomy` flag) with three levels:

| Level | Human gates | Failing stage checks | Skipped-stage gap |
|---|---|---|---|
| `gated` (default) | Stop for approval (exit `10`) | Block (exit `1`) | Block (exit `1`) |
| `auto` | Auto-approved, recorded as `auto-approved` | Block (exit `1`) | Block (exit `1`) |
| `yolo` | Auto-approved, recorded as `auto-approved` | Downgraded to warnings; advance with receipt result `pass-with-warnings` | Block (exit `1`) |

Two invariants hold at every level:

1. **A fully skipped stage always hard-stops.** If an upstream stage's
   `output/` is empty while a later stage is populated, the sequence
   guard fails even under `yolo`. An entire missing stage is a
   structural-integrity floor, not a quality preference.
2. **Auto-approved gates are auditable.** They are written as
   `auto-approved` (never `approved`) in `RESUME.md` and the receipt, so
   a reviewer can always tell which gates a human never actually saw.
   `verify_gate_approval.py` (the stricter CI-side check) still requires
   a literal `approved`, so a CI profile can reject auto-approved gates.

The agent must **never** raise the autonomy level itself. It is set by
the human in `clad.properties` or by an explicit in-conversation
instruction. When autonomy is anything other than `gated`, `advance.py`
prints a prominent banner and the agent states so plainly to the human.

## The stage contract

Each stage's `CONTEXT.md` follows the standard shape in
[`../../templates/stage-CONTEXT.md`](../../templates/stage-CONTEXT.md):
**Inputs / Process / Outputs / Verify / Gate**.

The `Inputs` table is **load-bearing**: an agent must load *exactly*
those files, no more. The `Outputs` list is closed: an agent must not
write files that are not on it.

The `Verify` section is also load-bearing: before requesting the human
gate, the agent must run every `Verify` item as a pass/fail self-audit.
If any item fails, the stage is not complete. The agent must stop,
surface the earliest invalid upstream stage or local defect, and ask to
reopen or repair it instead of normalizing the mismatch downstream.

When a stage depends on configuration or profile-specific commands, use
this precedence order unless the stage contract states otherwise:

1. feature-local `_config/` files named in the stage `Inputs`
2. `clad.properties` at the repo root for executable command values only
3. reference-profile docs for patterns and conventions only

If the needed value is still missing after that order, stop and ask the
human instead of guessing from examples or `.example` files.

## Stage-by-stage

Each stage's authoritative contract — inputs, process, outputs, verify
checks, and gate rules — lives in that stage's `CONTEXT.md` file. The
files below are the single source of truth for per-stage instructions:

| Stage | CONTEXT.md path (relative to feature root) | Produces | Gate |
|---|---|---|---|
| 00 | `../../features/_system/stages/00_actor-goal/CONTEXT.md` *(system scope)* | `actors.md`, `goals.md`, *(optional)* `port-spec.md` | 00 — system-level |
| 01 | `stages/01_usecase/CONTEXT.md` | `usecase.md` | Auto → 02b |
| 02a | `stages/02a_responsibility-map/CONTEXT.md` | `responsibility-map.md` | Auto → 02b |
| 02b | `stages/02b_chain-table/CONTEXT.md` | `<scenario>-chain.md` per scenario | **Gate 1 (Requirements)** |
| 02 | `stages/02_concepts/CONTEXT.md` | `<Name>.concept.md` per business concept | Auto → 03b |
| 03 | `stages/03_syncs/CONTEXT.md` | `<name>.sync.md` per coordination rule | Auto → 03b |
| 03a | `stages/03a_dependency-review/CONTEXT.md` | `<concept>-card.md` + `pattern-d-summary.md` | Auto → 03b |
| 03b | `stages/03b_data-model/CONTEXT.md` | `<Name>.data-model.md` per concept | **Gate 2 (Architecture)** |
| 04a | `stages/04_implement/04a_storage-mapping/CONTEXT.md` | `<Name>.storage.md` or `_NOT_APPLICABLE.md` | Auto → 04c |
| 04b | `stages/04_implement/04b_spec/CONTEXT.md` | `<Name>.spec.md` per concept | Auto → 04c |
| 04c | `stages/04_implement/04c_flow-tests/CONTEXT.md` | `.feature` files + step definitions | **Gate 3 (Executable)** |
| 04d | `stages/04_implement/04d_concept-tdd/CONTEXT.md` | Router → `04d_red-tests/` then `04d_green-impl/` | Auto → 05 |
| 04e | `stages/04_implement/04e_sync-tdd/CONTEXT.md` | Router → `04e_red-tests/` then `04e_green-impl/` | Auto → 05 |
| 05 | `stages/05_verify/CONTEXT.md` | `trace.md`, `findings.md`, `smoke.md`, `tracking.md` | Auto (close) |

### What each stage group demands of the model

| Stage group | Stages | Required capability | Fence |
|---|---|---|---|
| **Requirements analysis** | 00–02b | Collaborative clarification, structured prose, use-case writing | No implementation code or test files |
| **Structural modelling** | 02–03b | Cross-concept consistency, chain-table derivation, sync authoring, dependency analysis | No implementation code or test files |
| **Implementation** | 04a–05 | Test-first discipline, spec-to-code fidelity, storage-layer compliance | Red phase: tests only. Green phase: implementation only |

Skill files under [`../../skills/`](../../skills/) provide on-demand stage guidance
for agent frameworks that support Agent Skills. Stage `02_concepts/`, for
example, has a companion at [`../../skills/clad-concept-design/SKILL.md`](../../skills/clad-concept-design/SKILL.md).

### Stage-specific rules

These rules apply to individual stages and do not appear in the
`CONTEXT.md` files or skill instructions:

- **Stage 00** is the only multi-turn collaborative stage. The agent
  proposes, asks clarifying questions, iterates, and writes only after
  the human signals agreement. It precedes the per-UC advance loop.
- **Stage 02b chain tables** are the canonical resolver for
  action/outcome disputes. If a sync spec disagrees with a chain table,
  the table wins.
- **Stage 03 sync names** must follow the compressed grammar:
  `When<TriggerConcept><TriggerAction><TriggerCompletion>Then<TargetConcept><TargetAction>[For<Scope>]`.
  See [`../architecture/SYNCHRONIZATIONS.md`](../architecture/SYNCHRONIZATIONS.md) §"Naming".
- **Stage 03a** is an audit stage — it copies tokens exactly, produces
  no new design, and surfaces drift back to the owning stage.
- **Stage 04 implements the outside-in TDD double-loop:** 04c is the
  outer red test (a flow), 04d and 04e are the inner red→green TDD on
  concepts and syncs.
- **Stage 04e imperative orchestration** is a fail condition. An
  implementation that branches on business conditions or coordinates
  domain calls in a `*Coordinator` class does not satisfy the sync
  contract.
- **Stage 04 bootstrap (`Web`) implementations** must remain
  transport-only: normalize input, invoke the flow root, await the
  response, translate output. No business-concept dependencies, no
  domain branching, no concept-state reads/writes in the controller.
- **Stage 05** is the closing of the contract loop. It proves runtime
  behaviour matches the use case (back-trace) and that the deployable
  artefact runs (smoke).



## Cross-stage consistency

Every stage's `Verify` section must include at least one
**cross-stage consistency check** — a check that the stage's output is
coherent with an earlier stage's output. Examples:

- Stage 02 verifies: every actor in `00_actor-goal/output/actors.md`
  whose goal is in-scope appears in at least one concept's
  operational principle.
- Stage 03 verifies: every named scenario in
  `01_usecase/output/usecase.md` is satisfied by at least one sync (or
  is explicitly a `Web`-only failure path).
- Stage 04d verifies: every action listed in `04b_spec/output/` has at
  least one test row in the test-intent derivation map.
- Stage 05 verifies: every flow token observed at runtime back-traces
   to a use-case scenario using captured runtime evidence, not only
   predicted token chains.

The cross-stage check is what gives ICM § 6.2's reversibility
property teeth: a downstream stage cannot silently drift from
upstream. The quality-gate scripts under `quality-gate/` automate these cross-stage checks deterministically. Each script validates one contract boundary (SPEC parity, outcome alignment, data-model structure, etc.) and runs between every auto-advance stage.

## Why numbered folders

The numbering is execution order. Renumbering a folder is how you
change the order; there is no orchestration code to edit. The
filesystem **is** the orchestrator.

## LLM handoff table — who provides what at each stage transition

The table below is the operational summary of the human↔agent
contract at each stage boundary. It is the answer to "what is the
human's job here, what is the agent's job, and what is the human
reviewing at the gate?" Read top to bottom for a single feature.

| Gate | Stages | Human provides | Agent produces | Human reviews at gate |
|---|---|---|---|---|
| **1 (Requirements)** | 01 → 02a → 02b | Project brief (Stage 00) | usecase.md, responsibility-map.md, chain-table.md | Actors/goals correct? Scenarios cover all flows? Concept boundaries right? Action chains plausible? |
| **2 (Architecture)** | 02 → 03 → 03a → 03b | Approved requirements | concept.md, sync.md, dep-cards, data-model.md | Concept state machines cover the chains? Sync coordination declarative? Pattern D reads intentional? Data model complete? |
| **3 (Executable)** | 04a → 04b → 04c | Approved architecture | storage.md, spec.md, .feature files | Tests capture the right scenarios and inputs? |
| **Auto (Delivery)** | 04d → 04e → 05 | (nothing — all upstream artefacts approved) | concept code, sync code, test code, trace.md, smoke.md, tracking.md | (none — script-checked: `mvn test` passes, quality-gate scripts pass) |
