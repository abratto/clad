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
2. local workspace runtime config (`.cline-clad-config` / `.roo-clad-config`)
   for executable command values only
3. reference-profile docs for patterns and conventions only

If the needed value is still missing after that order, stop and ask the
human instead of guessing from examples or `.example` files.

## Stage-by-stage

### Stage 00 — `00_actor-goal/`

**Special semantics — collaborative.** This is the only stage whose
process is intentionally multi-turn.

**Input:** the human's brief.

**Process:** the agent **proposes** an initial actor/goal list from the
brief, then **asks targeted clarifying questions** (max 5 at a time),
iterates with the human, and only writes the final `actors.md` and
`goals.md` once the human signals agreement. The agent does not
fabricate goals beyond what the human confirms.

**Output:** `actors.md`, `goals.md` (per
[`../../templates/actors.md`](../../templates/actors.md) and
[`../../templates/goals.md`](../../templates/goals.md)).

**Gate:** human approval — but the gate is *expected* to take multiple
turns to reach.

### Stage 01 — `01_usecase/`

**Input:** `00_actor-goal/output/`, the human's brief.

**Process:** draft `usecase.md` with: a one-paragraph operational
principle for the *feature* (not for any single concept); the actors
(carried forward from stage 00); and the named scenarios the feature
must satisfy. Each scenario is a trigger + expected outcomes. Out of
scope is non-empty.

An optional Mermaid `sequenceDiagram` may appear inside a scenario as a
derived interaction sketch for humans. It is explanatory only and does
not become a new source of truth: Stage 01 prose remains canonical, and
Stage 02b chain tables remain the first canonical executable rendering
of cross-concept choreography. Stage 01 sequence diagrams stay limited
to actor/system interaction and must not introduce concept names, sync
names, provenance details, or state claims that are not already stated
in the prose use case.

Default expectation: include the sequence diagram when it materially
improves review clarity, especially for scenarios with branching
extensions, opaque failure handling, or longer interaction sequences.
Omit it when it would only restate a short linear path without adding a
useful visual distinction.

**Output:** `usecase.md`.

**Gate:** the human edits the use case before stage 2. If a sequence
diagram is present, the human checks that it improves clarity without
becoming a second design source; if a scenario obviously benefits from
one and none is provided, the human may send Stage 01 back for a more
legible presentation.

### Stage 02a — `02a_responsibility-map/`

**Input:** `01_usecase/output/usecase.md`,
`templates/responsibility-map.md`.

**Process:** identify the *concept set* the feature requires (one
capability each). Produce one row per concept naming its owned state
(one line) and its owned actions (names only — no signatures yet).
Then run the *coverage check*: list each scenario from the use case
and mark which concepts it touches. Anything that does not fit goes
in *Out of scope*.

**Output:** `responsibility-map.md`.

**Gate:** the human reviews the concept boundary set **before** any
cross-concept choreography is drawn or any per-concept anatomy is
written.

### Stage 02b — `02b_chain-table/`

**Input:** `01_usecase/output/usecase.md`,
`02a_responsibility-map/output/responsibility-map.md`,
`templates/chain-table.md`.

**Process:** for each named scenario in the use case, draw the chain
of concept actions that fulfils it as a numbered table
(`# | Concept | Action | Inputs | Outcome | Why this step`) plus a
Mermaid `stateDiagram-v2` diagram. The first row is always
`Web.handle`; the last row is always `Web.respond`.

At this level, `Concept + Action` is the concrete rendering of the
WYSIWID Level 2b **Then**. The corresponding **When** is still
implicit: row 1 is triggered by the use-case request, and each later
row is triggered by the previous row's outcome plus branch context.
`Inputs` name the downstream action's arguments only; they are **not**
join provenance. `Where`/pattern A/B/C/D first appear in Stage 03.

The chain table is therefore the bridge between 02a (which concepts
exist) and 03 (which syncs coordinate them).

**Output:** `<scenario>-chain.md` per scenario.

**Gate:** the human checks each chain is plausible and that no chain
introduces a concept absent from the responsibility map.

A well-formed chain table is structurally equivalent to a finite
state machine (states = outcomes, events = the outcome the previous
row emitted, transitions = the next row's action). The table is the
canonical source; any Mermaid diagram is **derived** from it and
must be presented in the **same conversation turn** as the table —
the gate cannot open over half a picture. See
[`../../templates/chain-table.md`](../../templates/chain-table.md)
§"The chain table is a finite state machine" for the FSM mapping and
the derivation rules.

### Stage 02 — `02_concepts/`

**Input:** `02a_responsibility-map/output/responsibility-map.md`,
`02b_chain-table/output/`, `methodology/architecture/CONCEPTS.md`,
`templates/concept.md`.

**Process:** for each concept already named in the responsibility
map, write the **full per-concept anatomy** in `<Name>.concept.md`:
state, actions (with signatures, outcomes, and flow-token
contributions), and an operational principle. Concepts whose
responsibilities are bootstrap-only (e.g. `Web`) get no concept file —
they are documented in `methodology/architecture/WEB_CONCEPT.md`. No
concept references another.

If a bootstrap concept file appears in `02_concepts/output/` without an
explicit methodology deviation, Stage 02 is not complete; the agent must
stop and reopen Stage 02 rather than carrying that file into downstream
stages.

**Output:** one `<Name>.concept.md` per business concept.

**Gate:** the human reviews the per-concept anatomy. The concept set
itself was already gated at 02a, so this gate focuses on action
shapes and outcomes.

### Stage 03 — `03_syncs/`

**Input:** `02_concepts/output/`, the use case (for the `Cites`
section), `methodology/architecture/SYNCHRONIZATIONS.md`,
`templates/sync.md`.

**Process:** for each scenario in the use case, identify the chain of
concept actions that fulfils it. Each coordination link becomes one
sync. Before writing sync prose, build a per-sync **Sync Contract
Matrix** from the approved 02b rows and 02 concept signatures: source
row id, target row id, exact `when`, exact `then`, and allowed literals.

Stage 03 is under an exact-token lock. Outcome names, argument names,
status values, casing, hyphenation, and numeric-vs-string literals must
match the approved earlier-stage contracts exactly. `where:` is for join
provenance only; it may not invent convenience payload fields. If any
02b row and 02 concept signature disagree, stop and reopen Stage 02
instead of guessing inside Stage 03.

**Output:** one `<name>.sync.md` per coordination rule.

**Gate:** the human checks that every scenario is covered, that no
sync contains imperative branching, that output filenames match the
stage's `Outputs` list exactly, and that any 02b↔02 signature mismatch
was surfaced as a Stage 02 correction rather than silently normalized in
the syncs.

### Stage 03a — `03a_dependency-review/`

**Input:** `03_syncs/output/`, `02b_chain-table/output/`,
`02a_responsibility-map/output/responsibility-map.md`,
`02_concepts/output/`,
[`../architecture/SYNC_PATTERNS.md`](../architecture/SYNC_PATTERNS.md),
[`../../templates/dependency-review-card.md`](../../templates/dependency-review-card.md),
[`../../templates/pattern-d-summary.md`](../../templates/pattern-d-summary.md).

**Process:** for each concept in 02a's map, produce a per-concept
dependency card listing (1) every action invocation it receives from
syncs, labelled by the data-flow pattern A/B/C/D from
[`../architecture/SYNC_PATTERNS.md`](../architecture/SYNC_PATTERNS.md),
and (2) every Pattern D read of its named region by other concepts.
Then produce a single `pattern-d-summary.md` consolidating every
Pattern D read in the feature.

Stage 03a is an audit stage, not a repair stage. Cards and the Pattern D
summary copy action names, argument names, field names, pattern labels,
keys, status codes, and literals exactly from the approved Stage 03
syncs. If 03a discovers token drift, it surfaces the defect and sends
work back to Stage 03 (or earlier if Stage 03 already reflects earlier
contract drift).

This stage produces no new design — it makes the cross-concept
coupling that already exists in the syncs **visible** so the human
can spot a flow-inconsistent invocation or an unintended state
coupling **before** Stage 04 turns it into code. Pattern D is the
only legal cross-concept read; if a flow appears to need data from
elsewhere, the dependency card is where that gets surfaced.

**Output:** `<concept>-card.md` per concept named in 02a's map;
`pattern-d-summary.md` consolidating Pattern D across the feature.

**Gate:** human approval. Last cross-concept sanity check before
implementation begins. The reviewer should reject any 03a artefact that
silently normalizes token mismatches instead of surfacing them.

### Stage 03b — `03b_data-model/`

**Input:** `02_concepts/output/`, `03a_dependency-review/output/`,
[`../architecture/DATA_MODEL_NOTES.md`](../architecture/DATA_MODEL_NOTES.md).

**Process:** for each approved concept spec, derive a profile-neutral
conceptual data model: fact types, uniqueness, mandatory roles, and
derived facts. Every fact must trace back to approved Stage 02 state or
approved Pattern D exposure from 03a. This stage decides the
**conceptual model**, not the storage technology.

**Output:** `<Name>.data-model.md` per concept.

**Gate:** human approval that the conceptual model is complete,
profile-neutral, and free of cross-concept schema coupling.

### Stage 04 — `04_implement/` (router)

`04_implement/CONTEXT.md` is a router: its **Process** points at the
five sub-stages below, and its **Outputs** list is empty (sub-stages
own all artefacts). Sub-stages run in order `04a → 04b → 04c → 04d →
04e`; the human gates after each.

#### Stage 04a — `04a_storage-mapping/`

**Input:** `03b_data-model/output/`, the chosen profile's reference
docs, [`../implementation/STORAGE_MAPPING.md`](STORAGE_MAPPING.md).

**Process:** if the profile uses a relational/RDF/document store, map
each approved conceptual data model into the profile's storage
primitives. Otherwise write `_NOT_APPLICABLE.md` explaining why and
skip.

Stage 04a must not invent new facts or constraints. It realizes the
approved model from 03b in a specific profile.

**Output:** `<Name>.storage.md` per concept (or `_NOT_APPLICABLE.md`).

**Gate:** human approval that the mapping honours R2 (one named region
per concept) and introduces no new design.

#### Stage 04b — `04b_spec/`

**Input:** `02_concepts/output/`, `templates/spec.md`.

**Process:** derive the SPEC contract slice mechanically from each
concept spec — action signatures, outcome enums, flow-token shape.
Nothing else.

If `02_concepts/output/` contains a bootstrap concept file such as
`Web.concept.md` without an explicit methodology deviation, `04b` must
stop and send work back to Stage 02 instead of deriving a SPEC from it.

SPEC files must not include correction history, methodology
interpretation, remediation notes, design commentary, or implementation
guidance beyond what is mechanically present in the concept spec.

**Output:** `<Name>.spec.md` per concept.

**Gate:** human approval. SPECs are what the implementation compiles
against.

#### Stage 04c — `04c_flow-tests/`

**Input:** `01_usecase/output/usecase.md`, `03_syncs/output/`,
`04b_spec/output/`, `features/UC-XX/_config/build-and-test.md`,
`features/UC-XX/_config/package-and-layout.md`.

**Process:** for each named scenario in the use case, write the
**outer** test as a markdown spec (HTTP request → expected sequence of
flow tokens → expected response), plus an explicit expected authored
action chain for that scenario, and a stub test under the chosen
profile's `src/test/.../flows/`. Tests start `@Disabled` (or red); they
go green only at the end of `04e`.

Stub flow tests live under the feature's configured
`APP_TEST_SOURCE_ROOT`; agents must not guess the test tree from the
reference profile when the feature config says otherwise.

One scenario means one markdown spec and one stub test file. A single
consolidated markdown file is not a substitute for the required
per-scenario artefacts.

Before claiming this stage is "red and ready", run the canonical
build-and-test command from `features/UC-XX/_config/build-and-test.md`
(or the targeted equivalent documented there) and verify the test tree
compiles. The expected outcome at this stage is either
disabled/skipped flow tests (when stubs are intentionally `@Disabled`)
or failing flow tests (if enabled early) — but never compilation
errors.

**Output:** `<scenario>-flow-test.md` per scenario; stub test files
under `reference-impl/<profile>/...`.

**Gate:** human reviews the flow predictions.

The `04c` artifact is therefore not only an output contract. It is also
the choreography contract that `04e` must satisfy when making the flow
green.

#### Stage 04d — `04d_concept-tdd/` (router)

**Input:** `02_concepts/output/`, `04b_spec/output/`,
`04c_flow-tests/output/`, `features/UC-XX/_config/build-and-test.md`,
`features/UC-XX/_config/package-and-layout.md`.

**Process:** route concept TDD through two structural child stages:

- `04d_red-tests/`: derive executable concept tests from approved outer
   artefacts, run them red, and record the handoff bundle
- `04d_green-impl/`: implement only against the approved red tests until
   they are green

Tests that depend on another concept's state or on sync orchestration do
not belong here; they belong in `04e`.

**Output:** child-stage outputs and side effects. `04d_red-tests/`
produces `concept-test-derivation.md`; `04d_green-impl/` produces green
concept code and tests in the selected profile.

**Gate:** `04d_red-tests/` approved before `04d_green-impl/` starts;
all approved concept tests green; no cross-concept imports.

#### Stage 04e — `04e_sync-tdd/` (router)

**Input:** `03_syncs/output/`, `04b_spec/output/`,
`04c_flow-tests/output/`, `features/UC-XX/_config/build-and-test.md`,
`features/UC-XX/_config/package-and-layout.md`.

**Process:** route sync TDD through two structural child stages:

- `04e_red-tests/`: derive executable sync tests from approved sync
   contracts, outer flow expectations, and the expected authored action
   chain from `04c`, run them red, and record the handoff bundle
- `04e_green-impl/`: implement only against the approved red sync tests
   until they are green and the flow tests from `04c` go green

There must be a 1:1 correspondence between approved Stage 03 sync specs
and Stage 04e test/implementation pairs. Do not invent extra executable
syncs with no upstream sync contract.

Imperative orchestration is a fail condition in Stage 04e. An
implementation does **not** satisfy the sync contract if it introduces a
class that sequences ordered domain calls, branches on business
conditions inline, or chooses the final response directly instead of
authoring the branch through concept outcomes and declarative syncs.
`*Coordinator` / `*Orchestrator` classes are therefore defects unless
they are thin profile/runtime adapters with an explicit methodology
waiver.

**Output:** child-stage outputs and side effects. `04e_red-tests/`
produces `sync-test-derivation.md`; `04e_green-impl/` produces green
sync code/tests and green flow tests.

**Gate:** `04e_red-tests/` approved before `04e_green-impl/` starts;
all sync tests green; flow tests from `04c` now green.

Gate evidence must include one executed build-and-test command result
showing: 1) test compilation succeeded, 2) sync tests are green, and
3) flow tests from `04c` are green.

Gate evidence must also show that green was reached through authorised
concept actions and declarative syncs rather than through imperative
scenario orchestration hidden in implementation code, and that the
runtime action chain matches the expected authored action chain written
in `04c`.

When the selected profile exposes a runtime debug surface, Stage 04 uses
that surface as the default tool for explaining observed behaviour while
the flow is still being made green. In the Java reference profile, this
means `/api/dev/flows`, `/api/dev/flow/{token}`, `/api/dev/stuck`, and
`/api/dev/concept/{name}/triples`. Predicted tokens and test comments
do not count as runtime evidence when such a surface exists.

For bootstrap / `Web` implementations, Stage 04 must also preserve the
transport boundary described in `WEB_CONCEPT.md`. A controller/route
handler may normalize input, invoke the flow root, await the authored
response, and translate transport output. It must not call business
concept classes directly, branch on domain outcomes, compute domain
policy, or read/mutate concept state.

### Stage 05 — `05_verify/`

Stage 05 has two parts: **Verify** (back-trace) and **Close** (smoke,
tracking, resume-point). The full contract is in the stage seed at
[`../../templates/feature-skeleton/stages/05_verify/CONTEXT.md`](../../templates/feature-skeleton/stages/05_verify/CONTEXT.md).

**Input:** the use case, the sync specs, a flow-token log from a
representative test execution, and the selected profile's runtime debug
surface when one exists.

**Process — verify:** for each named scenario, walk the flow-token
tree and check that it matches the chain of syncs and concept actions
the specs predict. Gather the runtime evidence for that walk from the
profile's debug surface when available; in the Java reference profile,
the default proof surface is `/api/dev/*`. Flag any tokens not
authorised by a spec. Also check that transport entry and transport exit
were reached through the authorised action/sync chain rather than being
short-circuited inside the controller / route handler.

**Process — close (only after verify is clean):**

1. Smoke the running profile (boot → exercise each scenario's trigger
   → record real responses) into `smoke.md`. This is the only step
   that proves the deployable artefact, not just the test suite,
   behaves.
2. Update tracking (or note "not applicable") into `tracking.md` —
   see [`../overlays/TRACKING.md`](../overlays/TRACKING.md) when the
   overlay is in use.
3. Append `Resume point: …` at the top of the trace file so the next
   session lands on a known next step.

**Output:** `trace.md` (with `Resume point:` line), `findings.md` if
anything failed verify, `smoke.md`, `tracking.md`.

**Gate:** any verify finding sends the loop back to whichever stage
owns the defect; closure has no further gate.

## Fast-path: when an agent may auto-advance

The default rule is **one stage per turn, gate after each**. There is
exactly one exception.

An agent may auto-advance through `04c → 04d → 04e` in a single turn
**if and only if** all four of the following hold:

1. The change is *behavioural* and was already gated through Stage 03
   in this session.
2. The agent produces a
   [`test-intent-derivation-map`](../../templates/test-intent-derivation-map.md)
   showing 1:1 traceability from each row in `04b_spec/output/` to a
   test it added or modified, and from each test back to a row.
3. No new concept and no new sync was introduced (R1, R2 unchanged).
4. The flow tests from `04c` end the turn green.

If any of (1)–(4) fails, fall back to one-stage-per-turn. The
fast-path exists to make small *behavioural* iterations bearable; it
never applies to *structural* changes (Stage 02a re-entry) or to a
feature's first run.

The human may always disable the fast-path by saying so.

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
upstream.

## Why numbered folders

The numbering is execution order. Renumbering a folder is how you
change the order; there is no orchestration code to edit. The
filesystem **is** the orchestrator.

## LLM handoff table — who provides what at each stage transition

The table below is the operational summary of the human↔agent
contract at each stage boundary. It is the answer to "what is the
human's job here, what is the agent's job, and what is the human
reviewing at the gate?" Read top to bottom for a single feature.

| Transition | Human provides | Agent produces | Human reviews at gate |
|---|---|---|---|
| brief → **00** | One-paragraph feature brief | Proposed actor list + ≤5 clarifying questions; iterates | Final `actors.md`, `goals.md` reflect what was agreed |
| 00 → **01** | Confirmed `actors.md`, `goals.md` | `usecase.md` at **Fully Dressed** level (op principle, scenarios, Postconditions Success+Failure mandatory) | Every in-scope goal has a named scenario; success+failure postconditions distinct |
| 01 → **02a** | Use case (Fully Dressed) | `responsibility-map.md` — one row per concept (state, actions), coverage check vs scenarios | Concept boundaries; scenarios are fully covered |
| 02a → **02b** | Responsibility map | One `<scenario>-chain.md` per scenario — action chain (table) **and** Mermaid diagram in the **same turn** | Each chain is plausible; no concept appears that wasn't in 02a |
| 02b → **02** | Responsibility map + chain tables | Per-concept `<Name>.concept.md` (full anatomy: state, actions, op principle); no cross-concept references | Concept anatomy honours R1; action outcomes cover the chains |
| 02 → **03** | Concept specs + chain tables | One `<name>.sync.md` per coordination rule; every `where` clause labelled with pattern A/B/C/D | Every scenario covered; no imperative branching; all joins explicit |
| 03 → **03a** | Sync specs + chain tables | One `<concept>-card.md` per concept; one `pattern-d-summary.md` for the feature | Cross-concept coupling is intentional; Pattern D is explicit and reviewed |
| 03a → **03b** | Sync specs + dependency review (Pattern D summary names every cross-concept field) | `<Name>.data-model.md` per concept — fact types and constraints under R2 | Conceptual state model supports the syncs; Pattern D reads map to named facts |
| 03b → **04a** | Data models + chosen profile | `<Name>.storage.md` per concept (or `_NOT_APPLICABLE.md`) | Profile mapping matches the conceptual model with no drift |
| 04a → **04b** | Storage mapping (or `_NOT_APPLICABLE.md`) + concept specs | `<Name>.spec.md` per concept (signatures, outcomes, flow-token shape) — mechanically derived | SPEC matches concept spec, no drift |
| 04b → **04c** | SPECs + use case | `<scenario>-flow-test.md` per scenario + stub red tests in profile | Predicted flow tokens match the scenario's postconditions |
| 04c → **04d** | SPECs + concept specs | `concept-test-derivation.md` + per-concept tests (red → green) + concept implementations | Tests trace 1:1 to SPEC rows; no cross-concept imports |
| 04d → **04e** | SPECs + sync specs | `sync-test-derivation.md` + per-sync tests (red → green); flow tests from 04c go green | All sync and flow tests green; `then` does no I/O outside concepts |
| 04e → **05** | Use case + running profile + runtime debug surface (if the profile exposes one) | `trace.md` (back-trace from flow tokens), `findings.md` if any, `smoke.md`, `tracking.md` | Every observed flow token traces back to a named scenario using captured runtime evidence |
