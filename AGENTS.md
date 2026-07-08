# AGENTS.md — Canonical guide for AI coding agents working in this repository

> This file is the **single source of truth** for any AI coding agent
> (Claude, Copilot, Cursor, Codex, etc.) operating on this repository.
> `CLAUDE.md`, `.github/copilot-instructions.md`, and `.cursor/rules/clad.mdc`
> are thin adapters that defer to this file.

---

## 1. What this repository is

CLAD is a discipline for building software with AI agents under human review.
It rests on three layers:

| Layer | What it controls | Where it lives |
|---|---|---|
| **CLAD** (process) | What changes are allowed, what shape they take | `methodology/core/` |
| **Legible / WYSIWID** (architecture) | How the running system is structured | `methodology/architecture/` |
| **ICM** (workspace) | How you walk a feature stage by stage | `methodology/implementation/STAGES.md`, `features/` |

You are expected to operate within all three layers simultaneously.

## 2. Operating principles (apply to every action)

1. **Read the contract first.** Before writing anything, open the relevant
   `CONTEXT.md` (workspace, then feature stage) and read its `Inputs`,
   `Process`, `Outputs` sections. Load only the files listed in `Inputs`.
   If a feature-local stage contract is stale relative to updated CLAD
   safety or sequencing rules in `methodology/` or the stage template,
   stop and refresh the feature-local contract before continuing that
   stage. Do not keep executing a stale copied contract once the drift is
   visible.
2. **Write to `output/` and stop at the gate.** Every stage ends with a
   review gate. After you write the stage's outputs, summarise what you
   produced and **wait** for the human to inspect/edit before moving on.
   When the human approves, advance to the successor named in this
   stage's `## Next stage` section (or, if absent, the next row of the
   table in §3). Open that stage's `CONTEXT.md` next, not before.
   "Ready for review" is not the same as "gate passed": a stage is ready
   for review after it passes self-audit, but the gate passes only when
   the human explicitly approves it.
3. **One stage, one job.** Do not run two stages in one turn. Do not
   anticipate the next stage's work in the current stage's output.
4. **No cross-concept references.** Code under `reference-impl/` and concept
   specs under `features/UC-*/stages/02_concepts/output/` must never
   reference another concept's state directly. Coordination happens only
   in syncs (stage `03_syncs/`).
5. **Edit the source, not the output, when a pattern repeats.** If you would
   make the same correction in three runs, the fix belongs in a
   `CONTEXT.md`, a reference file, or a template — not in the latest
   output. Surface this to the human.
6. **Cite when you adapt.** If you reuse ideas from Meng & Jackson or Van
   Clief, point to `methodology/reference/CITATIONS.md`.
7. **Branch rule.** Before writing any Stage 01 output, create and push
   the feature branch:
   `git checkout -b feat/UC-XX-<slug> && git push -u origin feat/UC-XX-<slug>`.
   Do not write artefacts to `main` directly.
8. **Commit rule.** After each of the three per-feature gates is approved
   by the human (Gate 1: 02b, Gate 2: 03b, Gate 3: 04c), commit all
   accumulated stage outputs since the last gate to the feature branch.
   Use a single commit per gate with a message like
   `feat(UC-XX): Gate 1 — requirements (stages 01–02b)`.
   The system-level Stage 00 is the only stage gated individually.
9. **RESUME rule.** After each gate is approved by the human, overwrite
   `features/UC-XX-<slug>/RESUME.md` with the current feature state
   (last completed stage, gate outcome, corrections, deferred concepts,
   next stage, next task). Do this before running the `git commit` for
   that gate. During an active stage, keep `RESUME.md` updated as
   working memory at the end of each turn (current blocker, failing
   command, files touched, next concrete steps).
10. **Intent routing rule.** Treat plain-language steering prompts as
      workflow intents:
      - If the human says "what's next" (or equivalent), diagnose the next
         actionable step from `ROADMAP.md` (if present), the active
         `features/UC-XX-<slug>/RESUME.md`, and the current stage gate
         status. Reply with one concrete next action, then wait for approval.
      - If the human says "let's work on a new feature" (or equivalent),
         run planning intake first: read `methodology/overlays/PLANNING.md`
         and check `plan-board.md` (if present) for priority/dependency fit.
         If Stage 00 outputs (`actors.md`/`goals.md`) do not exist, run
         system-scope Stage 00 first. If they do exist, planning is optional:
         either sequence via `plan-board.md` or pick an existing approved goal
         directly. Ask one targeted planning question if sequencing is unclear.
      - If intent is ambiguous, ask one clarifying question, then continue.
11. **Gate summary rule.** At each human gate (Gate 0 at Stage 00,
    Gate 1 at 02b, Gate 2 at 03b, Gate 3 at 04c), before presenting the
    approval question, list every artefact file produced since the last
    gate grouped by stage with a one-line description. The human must
    be able to identify what to review without inspecting the filesystem
    or `git diff`.
12. **Advance rule (gate-driven transitions).** You do **not** decide
    what stage comes next, and you do **not** open the next stage's
    `CONTEXT.md` on your own initiative. After you finish a per-UC stage
    (01–05) and its `output/` is written, end your turn by running:

    ```
    python3 quality-gate/advance.py --feature features/UC-XX-<slug>
    ```

    Treat that script's stdout as your next instruction. It runs the
    stage's `Verify` checks and the sequence/entry guard, writes a
    receipt, and then either (a) prints the next stage's `CONTEXT.md`
    path and a ready prompt, (b) stops you at a human gate with the
    artefact summary and the approval command, or (c) prints the
    specific defects and a correction prompt for the current stage. If
    it blocks (exit 1) or stops at a gate (exit 10), you must not
    advance. Only after `advance.py` prints a NEXT STAGE block may you
    open that stage. Stage 00 (system scope) is exempt — it is the
    collaborative intake stage and precedes the per-UC advance loop.
    See [`methodology/implementation/STAGES.md`](methodology/implementation/STAGES.md)
    §"Gate-driven advance".
13. **Autonomy rule (never self-select).** `advance.py` supports an
    opt-in autonomy override (`workflow.autonomy` in `clad.properties`,
    or the `--autonomy` flag / `CLAD_AUTONOMY` env). Its three levels are
    `gated` (default — every human gate stops for approval), `auto`
    (human gates are auto-approved but failing checks still block), and
    `yolo` (human gates auto-approved **and** failing checks are
    downgraded to warnings). You must **never** enable `auto` or `yolo`
    yourself, and never pass `--autonomy` to raise the level. This is a
    human-only decision, set by the operator in `clad.properties` or
    given as an explicit in-conversation instruction. Even under `yolo`,
    a fully skipped stage (an empty artefact-chain gap) remains a hard
    stop. Auto-approved gates are recorded as `auto-approved` (not
    `approved`) in `RESUME.md` and the receipt, so an auditor can tell a
    human never reviewed them. If autonomy is anything other than
    `gated`, say so plainly to the human at the start of the run.

## 3. The CLAD contract loop

Every meaningful change moves through this loop. Skipping a step is a bug.

```
  actor/goal -> use case -> concepts -> syncs -> data-model -> implement -> verify
     ^                                                       (04a..04e)        |
      +-------------------- back-trace from flow tokens ------------+
```

Mapped to the ICM stages of a feature folder:

> **Scope note:** Stage 00 runs **once per system brief** at
> `features/_system/stages/00_actor-goal/`. Stages 01–05 run **once per
> in-scope goal**, each in its own `features/UC-XX-<slug>/` folder.
> UC folders are created *after* Stage 00's gate is passed — one folder
> per confirmed in-scope goal from `goals.md`.

| Stage | Folder | Produces | Gate |
|---|---|---|---|
| 0 | `features/_system/stages/00_actor-goal/` *(system scope — run once per brief)* | `actors.md`, `goals.md`, *(optional)* `port-spec.md` when an externally imposed adapter contract exists (collaborative — see [`methodology/implementation/STAGES.md`](methodology/implementation/STAGES.md)) | `00 — system-level` |
| 1 | `stages/01_usecase/` | `usecase.md` (operational principle, actors, scenarios) | Auto¹ → 02b |
| 2a | `stages/02a_responsibility-map/` | `responsibility-map.md` (one row per concept: state, actions) | Auto¹ → 02b |
| 2b | `stages/02b_chain-table/` | `<scenario>-chain.md` per use-case scenario (action choreography) | **Gate 1 (Requirements)** |
| 2 | `stages/02_concepts/` | One `*.concept.md` per concept (full anatomy) | Auto¹ → 03b |
| 3 | `stages/03_syncs/` | One `*.sync.md` per coordination rule | Auto¹ → 03b |
| 3a | `stages/03a_dependency-review/` | One `*-card.md` per concept + `pattern-d-summary.md` (cross-concept coupling surface) | Auto¹ → 03b |
| 3b | `stages/03b_data-model/` | One `*.data-model.md` per concept (profile-neutral conceptual data model) | **Gate 2 (Architecture)** |
| 4 | `stages/04_implement/` | Router; top-level sub-stages `04a_storage-mapping`, `04b_spec`, `04c_flow-tests`, `04d_concept-tdd`, `04e_sync-tdd`, where `04d` and `04e` each split into structural red/green child stages | Auto¹ → 04c |
| 4a | `stages/04a_storage-mapping/` | Storage mapping (profile-specific) | Auto¹ → 04c |
| 4b | `stages/04b_spec/` | Spec. When `port-spec.md` exists, `spec.md` must include exact response shape examples (JSON path, field type, error envelope) for every HTTP endpoint, not only field presence. | Auto¹ → 04c |
| 4c | `stages/04c_flow-tests/` | Flow tests (outer red) | **Gate 3 (Executable)** |
| 4d | `stages/04d_concept-tdd/` | Concept TDD (inner red→green) | Auto → 05 |
| 4e | `stages/04e_sync-tdd/` | Sync TDD (inner red→green) | Auto → 05 |
| 5 | `stages/05_verify/` | Trace from running behaviour back to `usecase.md`, plus closure (smoke + tracking) | Auto (close) |

¹ Auto-advance means the agent proceeds to the immediate next stage without a
human gate. The name after `→` is the next human gate stage, not the immediate
next stage. Consult each stage's `## Next stage` section for the actual
successor.

Stage 04 is the **outside-in TDD double-loop**: `04c` is the outer red
test (a flow), `04d` and `04e` are the inner red→green TDD on concepts
and syncs. Stage 03b owns conceptual data modeling; Stage 04a owns only
profile-specific storage mapping and is optional for in-memory profiles.

Stage 00 has special semantics: the agent **proposes**, **asks ≤5
clarifying questions**, iterates with the human, and only writes
`actors.md` / `goals.md` once the human signals agreement.

## 4. The five-layer context hierarchy (ICM)

When you start work, identify which layer each file belongs to:

| Layer | Question it answers | Examples |
|---|---|---|
| 0 | "Where am I?" | This file (`AGENTS.md`) |
| 1 | "Where do I go?" | `CONTEXT.md` at repo root |
| 2 | "What do I do *here*?" | `features/UC-XX/stages/NN_*/CONTEXT.md` |
| 3 | "What rules apply?" (stable) | `methodology/`, `templates/`, `_config/` |
| 4 | "What am I working on?" (per-run) | `features/UC-XX/stages/NN_*/output/` |

Load Layers 0–2 always. Load Layer 3 only as the stage `Inputs` table
specifies. Layer 4 is what you produce or consume between stages.

## 4a. Project-wide configuration (`clad.properties`)

The file `clad.properties` at the repo root holds global defaults for
settings that affect how stages are run. It is framework-agnostic —
any agent (Cline, Copilot, Cursor, Roo, Codex, …) reads it at workspace
load.

Current keys:

| Key | Values | Purpose |
|---|---|---|
| `test.command` | Shell command | The single command to run tests for this profile |
| `storage.layer` | Free text | Describes the persistence technology in use |
| `stages.usecase.require-sequence-diagram` | `true` or `false` | Whether Mermaid sequence diagrams are required in Stage 01. Default `true`. Set to `false` if the LLM struggles with diagram generation. |
| `workflow.autonomy` | `gated`, `auto`, or `yolo` | How `advance.py` handles human gates and check failures. `gated` (default) stops at every gate; `auto` auto-approves gates but checks still block; `yolo` auto-approves gates and downgrades check failures to warnings. A skipped-stage gap always hard-stops. Human-only setting — agents must never raise it. |

**Resolution order** (lower number wins):

1. `clad.properties` (repo root) — project-wide default
2. `features/UC-XX/_config/<key>.md` — per-feature override
3. Stage-level `CONTEXT.md` — stage-specific override (when explicitly
   documented)

**Resolution order** (lower number wins):

1. `clad.properties` (repo root) — project-wide default
2. `features/UC-XX/_config/<key>.md` — per-feature override
3. Stage-level `CONTEXT.md` — stage-specific override (when explicitly
   documented)

Outer flow tests at Stage 04c use Cucumber/BDD (Gherkin `.feature` files
+ step definitions) — see `methodology/architecture/GHERKIN_INTEGRATION.md`.

## 4b. Agent Skills

CLAD ships portable, on-demand expertise packages as [Agent Skills](https://agentskills.io)
under the `skills/` directory. Each skill is a folder containing a
`SKILL.md` file with YAML frontmatter and Markdown instructions.

Skills use **progressive disclosure**:
1. **Metadata** — the agent's system prompt carries every skill's `name`
   and `description` (~100 tokens each).
2. **Instructions** — loaded on-demand when a task matches a skill's
   description.
3. **Resources** — referenced files loaded only when needed.

Stage `CONTEXT.md` Inputs tables list skill names alongside file paths.
Agents that support Skills discover them automatically; agents that do
not fall back to the raw file paths. The stage contract chain is
unchanged — skills replace only the "how to perform task X" instructions,
not the "what must be produced" contract.

Current skills:

| Skill | Loaded at |
|---|---|
| `clad-system-scoping` | Stage 00 |
| `clad-usecase-authoring` | Stage 01 |
| `clad-responsibility-mapping` | Stage 02a |
| `clad-chain-table` | Stage 02b |
| `clad-concept-design` | Stage 02 |
| `clad-sync-design` | Stage 03 |
| `clad-dependency-review` | Stage 03a |
| `clad-data-modeling` | Stage 03b |
| `clad-storage-mapping` | Stage 04a |
| `clad-spec-extraction` | Stage 04b |
| `clad-flow-testing` | Stage 04c |
| `clad-concept-tdd` | Stage 04d |
| `clad-sync-tdd` | Stage 04e |
| `clad-verification` | Stage 05 |
| `clad-handover` | Any session start |
| `clad-quality-gate` | Between stages |

## 5. Hard rules

These are non-negotiable. Violating any of them is a defect.

1. **No concept imports another concept.** In code: no Java import across
   concept packages. In specs: no `*.concept.md` mentions another concept's
   state by name. Cross-concept coordination is only legal inside syncs.
2. **One named persistence region per concept.** When concepts persist state (e.g. via
   RDF/Jena under the Java profile), each concept owns its graph; no
   concept reads another's graph directly.
3. **Syncs are declarative, not imperative.** A sync says
   `when X completes -> then Y`. It does not contain branching business
   logic; that belongs in a concept's actions.
4. **`Web` (or equivalent HTTP entry) is the sole bootstrap concept.**
   No business concept owns an HTTP endpoint.
5. **Every action emits a flow token.** A flow token is a small,
   addressable record (id, who, when, what) that lets `05_verify/` trace
   from a runtime effect back to the use case.

Additional hard rules:

- **R14 — Concept unit tests MUST assert field values, not only outcome tokens.**
   A test that only checks `outcome == "FOUND"` is insufficient. Every
   concept unit test must assert at least the primary output fields of
   `writeCompletion` (e.g. `slug`, `title`, `userId`) to catch silent
   field-mapping bugs.
- **R15 — Every sync that fires on a shared trigger MUST declare its route scope.**
   A sync whose trigger action can be produced by more than one flow
   (e.g. `User/getProfile[FOUND]`) must either carry an explicit route
   filter via `parameterizeSparql`, or carry a documented justification
   for why it is intentionally route-agnostic. This property must be
   verified at Stage 03a.

Rules R1–R5 above are the WYSIWID architectural rules. Four additional
process/discipline rules (R6–R9) are defined in
[`methodology/implementation/RULES.md`](methodology/implementation/RULES.md)
and are equally binding. R14 and R15 above are additional hard rules for
the testing and dependency-review stages. Hard-learned implementation
rules in §9 (R10–R13 and R16–R17) are equally binding. Stage CONTEXT.md
Inputs tables reference the full rule set as needed.

If a rule appears to be in conflict with a request, **stop and ask** —
do not silently relax it.

## 6. Rejection protocol

When the human rejects a stage's output (says "no", "this is wrong",
edits something materially, or asks for a redo), follow exactly these
three steps. Do not freelance.

1. **Acknowledge what was rejected.** Restate, in one sentence, the
   specific artefact or decision the human pushed back on. Do not
   apologise; do not re-explain the rationale unless asked.
2. **Ask one targeted clarifying question** — at most one — before
   redoing anything. The question should be the *smallest* one whose
   answer disambiguates the redo. If the rejection was already
   unambiguous (e.g. the human edited the output directly), skip this
   step.
3. **Re-run the same stage.** Produce a new `output/` for the stage
   you were on. Do **not** silently advance to the next stage. Do
   **not** drop back to an earlier stage unless the human explicitly
   said to. Stop at the gate again.

This protocol is what keeps rework predictable. Without it, agents
fall back on general LLM instinct — re-explaining, over-apologising,
sometimes producing a different artefact entirely — which makes the
human's next decision harder, not easier.

When rejection occurs at any of the three per-feature gates, the defect
may belong to any stage within that gate's block. The agent re-runs the
earliest stage that owns the defect, not the entire gate block.

## 7. Capability profiles

CLAD is model-agnostic. The table below describes the **reasoning
capability** each stage group requires. Map these to whatever models
or agents you have available — the names and providers are your
operator concern, not CLAD's.

| Stage group | Stages | Required capability | Fence |
|---|---|---|---|---|
| **Requirements analysis** | 00–02b | Collaborative clarification, structured prose, use-case writing. Depth of reasoning matters less than fluency and willingness to iterate with the human. | No implementation code or test files |
| **Structural modelling** | 02–03b | Cross-concept consistency, chain-table derivation, sync authoring, dependency analysis. This is the hardest reasoning load in CLAD — use your strongest model here. | No implementation code or test files |
| **Implementation** | 04a–05 | Test-first discipline, spec-to-code fidelity, storage-layer compliance. Needs strong code generation and the ability to follow multi-step TDD sequences without drifting. | Red phase: tests only, no implementation. Green phase: implementation only, do not rewrite approved tests |

> **Operator note:** if you run CLAD with a local setup (e.g. Continue +
> Roo in VS Code), create a local config file (outside this repo) that
> maps these capability profiles to your specific models. Do not commit
> model names or plugin configuration into CLAD itself — that is
> operator-level configuration, not methodology.

## 8. When you are stuck

- If the stage `CONTEXT.md` is ambiguous, edit the `CONTEXT.md` first
  (with the human's approval) and *then* run the stage.
- If you produced output that you cannot trace back to a concept or sync,
  you are mid-violation of rule 1. Stop and surface the problem.
- If the human has edited a previous stage's output, **re-read it**.
  Treat the edit as authoritative.

## 9. Critical Context — hard-learned implementation rules

These rules come from defects discovered while implementing 13 Conduit
use cases. They supplement §5 and are equally binding.

### R10 — Sync SPARQL variables MUST use the engine's reserved names

`SyncAgent.assembleSparql()` binds three variables in the outer `WHERE` /
`INSERT` shape: `?_when_1` (trigger action node), `?_flow` (flow token),
`?_then_1` (new invocation). Subclass `whereClause()` and `thenBindings()`
MUST use exactly these three names. Never introduce synonyms
(`?_w`, `?_f`, `?article`). Using a different flow variable causes
`?_then_1 :flow ?_flow` to write the wrong flow token; using a different
trigger variable causes the dedup guard to mark the wrong node. See
`reference-impl/java-micronaut-jena/CODE_STYLE.md` § "Reserved variable
names".

### R11 — Every sync that fires on a shared business-concept action MUST filter by route

`Session/grant[GRANTED]` fires for login, sign-in, AND register flows.
If a respond sync does not include `?_root :route ?_route` with a
`bindLiteral` in `parameterizeSparql`, it will fire for all three flows,
producing wrong HTTP status codes (e.g., login returning 200 instead of
register's 201). Syncs that trigger on `Web/request` already have the
route — others MUST add it. See
`reference-impl/java-micronaut-jena/CODE_STYLE.md` § "Must filter by
route".

### R12 — Concept writeCompletion MUST write a plain `:outcome` triple

`ConceptAgent.findPendingInvocations()` uses
`FILTER NOT EXISTS { ?_action :outcome ?_any_outcome }` to skip
already-processed actions. Without a plain `:outcome` triple, the filter
never matches the RDF-star annotation, and completed actions are
re-processed (causing e.g. duplicate user registrations, runaway sync
firing). The RDF-star `<< action :outcome VALUE >>` annotation is
separate and used by syncs for outcome matching. Both forms are required.

### R13 — Jackson must serialize null values (`Include.ALWAYS`)

CLAD syncs author field-value maps where missing fields imply null.
Jackson's default `NON_NULL` omits these fields, making Conduit spec
assertions like `jsonpath "$.user.bio" == null` fail with `none` not
`null`. Configure `jackson.serialization-inclusion: always` in
`application.yml` or equivalent for your profile. See `clad.properties`
for the canonical setting.

### R16 — Stage 04d tests must assert completion field values

`writeCompletion` writes named fields that downstream syncs consume. If
a field-mapping bug exists (wrong variable name, PSS substitution
collision, missing SPARQL binding), an outcome-only test will pass while
all downstream consumers receive null or empty values. The minimum for
any concept unit test:

- Assert the `outcome` value.
- Assert the primary fields the concept's `writeCompletion` writes.
- Assert that no primary field is null or empty string when the inputs
   are valid.

### R17 — Every change to a sync or concept MUST re-enter the CLAD stage pipeline

`methodology/core/ITERATIVE_CHANGES.md` is binding. Before modifying any
file that falls under:

- `features/UC-*/stages/02_concepts/output/` (concept specs)
- `features/UC-*/stages/03_syncs/output/` (sync specs)
- any profile's implementation source for concepts or syncs
  (e.g. `app/backend/src/.../{concepts,syncs}/`,
   `reference-impl/java-micronaut-jena/src/.../concepts/` or `.../syncs/`)

the agent MUST:

1. Open `methodology/core/ITERATIVE_CHANGES.md` and classify the change
   (Presentation / Behavioural / Structural).
2. Identify the earliest stage whose `output/` is no longer accurate and
   re-enter there.
3. Update all affected stage artefacts (sync specs, concept specs, chain
   tables) in the **same commit** as the implementation change.

A Java sync class with no corresponding `*.sync.md`, or a Java concept
class whose outcomes no longer match the approved `*.concept.md`, is a
defect of the same severity as a cross-concept import (R1).

`quality-gate/verify_implementation_parity.py` mechanises the
implementation-to-artefact direction of this rule: it fails if an
implementation class exists with no corresponding spec artefact, or if a
sync spec/class/runtime name does not lower mechanically from the Stage 03
sync rule. `quality-gate/verify_sync_implementation_parity.py` mechanises
the artefact-to-implementation direction for syncs: it fails if any Stage
03 sync contract has no corresponding Stage 04e `SyncAgent` implementation.
`quality-gate/verify_iterative_change_readiness.py` mechanises the intake
direction: when the diff touches concept/sync specs or implementation, it
fails unless an `_changes/` artefact records the change category, earliest
re-entry stage, artefact-impact matrix, and re-derivation order.
`quality-gate/verify_iterative_change_coupling.py` mechanises the same-batch
direction: it fails if a concept/sync implementation changes without its
matching Stage 02/03 artefact changing in the same diff.

## 10. Pointers

- Methodology reading order: [`methodology/README.md`](methodology/README.md)
- Worked example: [`features/UC-00-login/README.md`](features/UC-00-login/README.md)
- New-feature bootstrap: [`templates/feature-skeleton/`](templates/feature-skeleton/) (copy this, do **not** copy `features/UC-00-login/`)
- Stage contract template: [`templates/stage-CONTEXT.md`](templates/stage-CONTEXT.md)
- Iterative-change workflow: [`methodology/core/ITERATIVE_CHANGES.md`](methodology/core/ITERATIVE_CHANGES.md)
- Pre-commit quality gate: [`methodology/implementation/QUALITY_GATE.md`](methodology/implementation/QUALITY_GATE.md)
- Trunk-based delivery + CI gate: [`methodology/implementation/DELIVERY.md`](methodology/implementation/DELIVERY.md)
- Handover protocol: [`methodology/implementation/HANDOVER.md`](methodology/implementation/HANDOVER.md)
- Optional workflow overlay: [`methodology/overlays/TRACKING.md`](methodology/overlays/TRACKING.md)
- Optional planning/intake shortcuts: [`methodology/overlays/PLANNING.md`](methodology/overlays/PLANNING.md)
- Optional decision log: [`methodology/overlays/DECISIONS.md`](methodology/overlays/DECISIONS.md)
- Optional local-model context overlay: [`methodology/overlays/LOCAL_LLM.md`](methodology/overlays/LOCAL_LLM.md)
- Agent Skills reference: [`skills/`](skills/)
- Citations: [`methodology/reference/CITATIONS.md`](methodology/reference/CITATIONS.md)
