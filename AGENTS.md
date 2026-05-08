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
2. **Write to `output/` and stop at the gate.** Every stage ends with a
   review gate. After you write the stage's outputs, summarise what you
   produced and **wait** for the human to inspect/edit before moving on.
   When the human approves, advance to the successor named in this
   stage's `## Next stage` section (or, if absent, the next row of the
   table in §3). Open that stage's `CONTEXT.md` next, not before.
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

## 3. The CLAD contract loop

Every meaningful change moves through this loop. Skipping a step is a bug.

```
  actor/goal -> use case -> concepts -> syncs -> implement -> verify
      ^                                          (04a..04e)        |
      +-------------------- back-trace from flow tokens ------------+
```

Mapped to the ICM stages of a feature folder:

| Stage | Folder | Produces |
|---|---|---|
| 0 | `stages/00_actor-goal/` | `actors.md`, `goals.md` (collaborative — see [`methodology/implementation/STAGES.md`](methodology/implementation/STAGES.md) §"Stage 00") |
| 1 | `stages/01_usecase/` | `usecase.md` (operational principle, actors, scenarios) |
| 2a | `stages/02a_responsibility-map/` | `responsibility-map.md` (one row per concept: state, actions) |
| 2b | `stages/02b_chain-table/` | `<scenario>-chain.md` per use-case scenario (action choreography) |
| 2 | `stages/02_concepts/` | One `*.concept.md` per concept (full anatomy) |
| 3 | `stages/03_syncs/` | One `*.sync.md` per coordination rule |
| 3a | `stages/03a_dependency-review/` | One `*-card.md` per concept + `pattern-d-summary.md` (cross-concept coupling surface) |
| 4 | `stages/04_implement/` | Router; sub-stages `04a_orm`, `04b_spec`, `04c_flow-tests`, `04d_concept-tdd`, `04e_sync-tdd` produce the artefacts and code |
| 5 | `stages/05_verify/` | Trace from running behaviour back to `usecase.md`, plus closure (smoke + tracking) |

Stage 04 is the **outside-in TDD double-loop**: `04c` is the outer red
test (a flow), `04d` and `04e` are the inner red→green TDD on concepts
and syncs. Stage 04a (ORM) is optional and skipped for in-memory
profiles.

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

## 5. Hard rules

These are non-negotiable. Violating any of them is a defect.

1. **No concept imports another concept.** In code: no Java import across
   concept packages. In specs: no `*.concept.md` mentions another concept's
   state by name. Cross-concept coordination is only legal inside syncs.
2. **One named graph per concept.** When concepts persist state (e.g. via
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

## 7. When you are stuck

- If the stage `CONTEXT.md` is ambiguous, edit the `CONTEXT.md` first
  (with the human's approval) and *then* run the stage.
- If you produced output that you cannot trace back to a concept or sync,
  you are mid-violation of rule 1. Stop and surface the problem.
- If the human has edited a previous stage's output, **re-read it**.
  Treat the edit as authoritative.

## 8. Pointers

- Methodology reading order: [`methodology/README.md`](methodology/README.md)
- Worked example: [`features/UC-00-login/README.md`](features/UC-00-login/README.md)
- New-feature bootstrap: [`templates/feature-skeleton/`](templates/feature-skeleton/) (copy this, do **not** copy `features/UC-00-login/`)
- Stage contract template: [`templates/stage-CONTEXT.md`](templates/stage-CONTEXT.md)
- Iterative-change workflow: [`methodology/core/ITERATIVE_CHANGES.md`](methodology/core/ITERATIVE_CHANGES.md)
- Pre-commit quality gate: [`methodology/implementation/QUALITY_GATE.md`](methodology/implementation/QUALITY_GATE.md)
- Trunk-based delivery + CI gate: [`methodology/implementation/DELIVERY.md`](methodology/implementation/DELIVERY.md)
- Optional workflow overlay: [`methodology/overlays/TRACKING.md`](methodology/overlays/TRACKING.md)
- Optional decision log: [`methodology/overlays/DECISIONS.md`](methodology/overlays/DECISIONS.md)
- Citations: [`methodology/reference/CITATIONS.md`](methodology/reference/CITATIONS.md)
