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

**If you are joining an existing project and cannot load CLAD skills,**
read these files directly instead: `AGENTS.md` §1–3, `CONTEXT.md`,
`methodology/implementation/HANDOVER.md`, and the active feature's
`RESUME.md`. See §4b for the full skill-to-file fallback table.

1. **Read the contract first.** Before writing anything, open the relevant
   `CONTEXT.md` (workspace, then feature stage) and read its `Inputs`,
   `Process`, `Outputs` sections. Load only the files listed in `Inputs`.
   If a feature-local stage contract is stale relative to updated CLAD
   safety or sequencing rules in `methodology/` or the stage template,
   stop and refresh the feature-local contract before continuing that
   stage. Do not keep executing a stale copied contract once the drift is
   visible.
   The per-stage file manifest lives in
   [`methodology/implementation/CONTEXT_MANIFEST.md`](methodology/implementation/CONTEXT_MANIFEST.md)
   — use it to confirm you are loading the right files, nothing more.
2. **Write to `output/` and stop at the gate.** Every stage ends with a
    review gate. After you write the stage's outputs, summarise what you
    produced and **wait** for the human to inspect/edit before moving on.
    After the human approves, end your turn by running `./clad advance`
    (or `python3 quality-gate/advance.py --feature features/UC-XX-<slug>`)
    — never self-select the next stage. "Ready for
    review" is not the same as "gate passed": a stage is ready for
    review after it passes self-audit, but the gate passes only when
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
   by the human (Gate 1: 01b, Gate 2: 03b, Gate 3: 04c), commit all
   accumulated stage outputs since the last gate to the feature branch.
   Use a single commit per gate with a message like
   `feat(UC-XX): Gate 1 — requirements (stages 01–01b)`.
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
    Gate 1 at 01b, Gate 2 at 03b, Gate 3 at 04c), before presenting the
    approval question, list every artefact file produced since the last
    gate grouped by stage with a one-line description. The human must
    be able to identify what to review without inspecting the filesystem
    or `git diff`.
12. **Advance rule (gate-driven transitions).** You do **not** decide
    what stage comes next, and you do **not** open the next stage's
    `CONTEXT.md` on your own initiative. After you finish a per-UC stage
    (01–05) and its `output/` is written, end your turn by running:
    ```
    ./clad advance
    ```
    (Long form: `python3 quality-gate/advance.py --feature features/UC-XX-<slug>`.)
    Treat that script's stdout as your next instruction — it runs the
    stage's `Verify` checks and the sequence/entry guard, then prints the
    next stage, stops at a human gate, or names defects. Only after it
    prints a NEXT STAGE block may you open that stage. Full mechanics:
    [`methodology/implementation/STAGES.md`](methodology/implementation/STAGES.md)
    §"Gate-driven advance". Stage 00 (system scope) is exempt.
13. **Workflow-control rule (never self-select).** `advance.py` supports
    two human-only, opt-in settings — `workflow.autonomous` (auto-approve
    the 3 gates, recorded `auto-approved`) and `workflow.session-per-stage`
    (stop + handoff after every stage). You must **never** enable either
    yourself or pass the flags to turn one on. This is a human-only
    decision, set in `clad.properties`. Full mechanics:
    [`methodology/implementation/STAGES.md`](methodology/implementation/STAGES.md)
    §"Workflow control".
14. **Self-audit rule.** At the end of every stage — including pure design
    stages 01–03b where no test framework runs — self-audit with:
    ```
    python3 quality-gate/verify_artefacts.py
    ```
    This runs the same artefact pipeline gate that `test.command` runs.
    If it fails, the stage is not complete. In implementation stages
    (04c–04e), `test.command` runs this gate automatically, so you do
    not need to invoke it separately.
15. **CLAD release rule.** When publishing this repository's CLAD distribution,
   a release is an annotated Git tag named `vMAJOR.MINOR.PATCH` on a green
   `main` commit, with a matching version section in `CHANGELOG.md`. Agents may
   prepare release notes and verify the candidate commit, but must not create
   or push a release tag unless the human explicitly authorizes the version and
   release. This rule does not govern releases of downstream CLAD-based
   projects; their maintainers define their own release policy.

## 3. The CLAD contract loop

Every meaningful change moves through this loop. Skipping a step is a bug.

```
  actor/goal -> use case -> concepts -> syncs -> data-model -> implement -> verify
     ^                                                       (04a..04e)        |
      +-------------------- back-trace from flow tokens ------------+
```

The full stage-to-folder map, gate placement, and auto-advance graph
live in [`methodology/implementation/STAGES.md`](methodology/implementation/STAGES.md)
§"Folder layout" and §"Stage-by-stage" — those tables are the canonical
reference and are not repeated here. The three essentials to remember:

- **System scope:** Stage 00 runs once per brief at
  `features/_system/stages/00_actor-goal/`, producing `actors.md`,
  `goals.md`, and optional `port-spec.md`.
- **Per-UC scope:** Stages 01–05 run once per in-scope goal, each in
  `features/UC-XX-<slug>/`. One folder per confirmed in-scope goal.
- **Gates:** Gate 1 (Requirements) at 01b, Gate 2 (Architecture) at 03b,
  Gate 3 (Executable) at 04c. Stages between gates auto-advance.
  Stages 04a–04e implement the outside-in TDD double-loop: `04c` is the
  outer red test (a flow); `04d`/`04e` are the inner red→green TDD on
  concepts and syncs.

Stage 00 has special semantics: the agent **proposes**, **asks ≤5
clarifying questions**, iterates, and only writes `actors.md` /
`goals.md` once the human signals agreement.

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

### 4a. Project-wide configuration (`clad.properties`)

The file `clad.properties` at the repo root holds global defaults for
settings that affect how stages are run. It is framework-agnostic and
self-documenting: each key's meaning, values, and profile-specific
notes are written inline in that file. Read `clad.properties` rather
than guessing a key. Resolution order (lower wins):

1. `features/UC-XX/_config/<key>.md` — per-feature override
2. `clad.properties` (repo root) — project-wide default
3. Stage-level `CONTEXT.md` — stage-specific override (when documented)

Two human-only workflow keys (`workflow.autonomous`,
`workflow.session-per-stage`) are described inline there and in
`STAGES.md` §"Workflow control". `test.command` there is the sole valid
test invocation (R19). The canonical `storage.layer` is
"In-memory FactStore relations (fire-after-commit engine)".

### 4b. Agent Skills (with fallback)

CLAD ships portable, on-demand expertise packages as [Agent Skills](https://agentskills.io)
under the `skills/` directory (each a folder with a `SKILL.md`).

**If your agent cannot load skills** (reports "skill not found" or only
lists built-in skills), read the corresponding raw files instead:

| Skill | Fallback files (read in order) |
|---|---|
| `clad-handover` (session start) | `AGENTS.md` §1–2, `CONTEXT.md`, `methodology/implementation/HANDOVER.md`, `features/UC-XX-<slug>/RESUME.md` |
| `clad-quality-gate` (between stages) | `methodology/implementation/QUALITY_GATE.md`, then the current stage's `CONTEXT.md` §Verify |
| Any stage skill (01–05) | The stage's `CONTEXT.md` and the files its `Inputs` table lists — load those directly, skip the skill |

The stage contract is authoritative and identical either way: a skill
adds on-demand guidance but never overrides the stage `CONTEXT.md`
`Inputs`/`Outputs`/`Verify`. Some skills are the required stage
guidance (`clad-sync-design`, `clad-concept-design`, `clad-concept-tdd`,
`clad-sync-tdd`); others are thin aggregators; each `SKILL.md` states
its own role in its header.

## 5. Hard rules — index

The full, binding text of every hard rule lives in
[`methodology/implementation/RULES.md`](methodology/implementation/RULES.md).
That file is authoritative; this section is an index only.

- **R1–R5 (WYSIWID architectural):** no concept imports another; one
  named persistence region per concept; syncs are declarative
  (`when … then …`) not imperative; one primary bootstrap adapter per
  transport surface; every action emits a flow token.
- **R6–R9 (process/discipline):** stage outputs written only by the
  owning stage; every running effect traces to a use case; outer-loop
  tests before implementation; every SPEC outcome maps to a distinct
  branch.
- **R10, R21 (retired):** kept as IDs only, with retirement notes.
- **R11–R20 (hard-learned implementation):** shared-trigger route
  scoping (R11); `outcome` field required (R12); Jackson
  `Include.ALWAYS` (R13); field-value test assertions (R14); Stage 03a
  route-scope verification (R15); Stage 04d completion-field assertions
  (R16); iterative-change re-entry (R17); mandatory quality gate at
  commit (R18); `test.command` only (R19); maintenance governance (R20).

Quality-gate scripts enforce R1–R5, R14–R20 mechanically — do not relax
any of them. If a rule appears to conflict with a request, **stop and ask**.

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

When rejection occurs at any of the three per-feature gates, the defect
may belong to any stage within that gate's block. The agent re-runs the
earliest stage that owns the defect, not the entire gate block.

## 7. Capability profiles

CLAD is model-agnostic. The **reasoning capability** each stage group
requires is tabulated in
[`methodology/implementation/STAGES.md`](methodology/implementation/STAGES.md)
§"What each stage group demands of the model". In short: Requirements
analysis (00–01b) needs fluency and iteration, not deep reasoning;
Structural modelling (02–03b) is the hardest load — use your strongest
model; Implementation (04a–05) needs strong code generation and
test-first discipline. Map these to your own models in a local config
file outside the repo — do not commit model/plugin configuration into
CLAD.

## 8. When you are stuck

- If the stage `CONTEXT.md` is ambiguous, edit the `CONTEXT.md` first
  (with the human's approval) and *then* run the stage.
- If you produced output that you cannot trace back to a concept or sync,
  you are mid-violation of R1. Stop and surface the problem.
- If the human has edited a previous stage's output, **re-read it**.
  Treat the edit as authoritative.

## 9. Pointer index

The hard-learned implementation rules R10–R21 (once inline here) now
live in [`methodology/implementation/RULES.md`](methodology/implementation/RULES.md).
Full pointers:

- Methodology reading order: [`methodology/README.md`](methodology/README.md)
- Stage map + gates: [`methodology/implementation/STAGES.md`](methodology/implementation/STAGES.md)
- Per-stage file manifest: [`methodology/implementation/CONTEXT_MANIFEST.md`](methodology/implementation/CONTEXT_MANIFEST.md)
- Hard rules: [`methodology/implementation/RULES.md`](methodology/implementation/RULES.md)
- Artefact dependency graph: [`methodology/architecture/ARTEFACT_MAP.md`](methodology/architecture/ARTEFACT_MAP.md)
- Artefact-to-code traceability: [`methodology/architecture/TRACEABILITY.md`](methodology/architecture/TRACEABILITY.md)
- Worked example: [`features/UC-00-login/README.md`](features/UC-00-login/README.md)
- New-feature bootstrap: [`templates/feature-skeleton/`](templates/feature-skeleton/) (copy this, do **not** copy `features/UC-00-login/`)
- Stage contract template: [`templates/stage-CONTEXT.md`](templates/stage-CONTEXT.md)
- Iterative-change workflow: [`methodology/core/ITERATIVE_CHANGES.md`](methodology/core/ITERATIVE_CHANGES.md)
- Pre-commit quality gate: [`methodology/implementation/QUALITY_GATE.md`](methodology/implementation/QUALITY_GATE.md)
- Trunk-based delivery + CI gate: [`methodology/implementation/DELIVERY.md`](methodology/implementation/DELIVERY.md)
- Handover protocol: [`methodology/implementation/HANDOVER.md`](methodology/implementation/HANDOVER.md)
- Optional overlays: [`TRACKING.md`](methodology/overlays/TRACKING.md), [`PLANNING.md`](methodology/overlays/PLANNING.md), [`DECISIONS.md`](methodology/overlays/DECISIONS.md), [`LOCAL_LLM.md`](methodology/overlays/LOCAL_LLM.md), [`PORTS_AND_ADAPTERS.md`](methodology/overlays/PORTS_AND_ADAPTERS.md)
- Agent Skills reference: [`skills/`](skills/)
- Citations: [`methodology/reference/CITATIONS.md`](methodology/reference/CITATIONS.md)
