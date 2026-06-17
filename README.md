# CLAD — Contract-Led, Artefact-Driven Development

> A starter repository for building software with AI coding agents under a
> discipline that keeps every decision **legible, reviewable, and reversible**.

CLAD combines three ideas that, taken together, let a single human reviewer
steer multi-step agent work without losing control of the system being built:

1. **CLAD (process)** — every change flows through *contracts* (small,
   reviewable specs) and produces *artefacts* (files on disk you can diff).
   No work happens off-contract; no artefact is born without a contract.
2. **Legible architecture (WYSIWID pattern)** — runtime is decomposed into
   independent **concepts** (small state machines with explicit operational
   principles) connected only by declarative **synchronizations**. What you
   read in a concept spec is what the running system does. Adapted from
   Meng & Jackson, *What You See Is What It Does* (Onward! 2025).
3. **ICM workspace scaffold** — each feature lives in its own folder of
   numbered stages (`01_usecase/`, `02_concepts/`, …). Each stage has a
   `CONTEXT.md` *contract* (Inputs / Process / Outputs) and an `output/`
   folder the human can inspect and edit before the next stage runs.
   Adapted from Van Clief, *Interpretable Context Methodology*.

```
actors/goals -> use case -> responsibility map -> chain tables ->
concepts -> syncs -> dependency review -> implement -> verify
   (00)        (01)        (02a)              (02b)
   (02)        (03)        (03a)              (04)        (05)
```

At every arrow there is a folder you can open, a `CONTEXT.md` contract
that tells the agent what to do, and an `output/` folder you can inspect
and edit before the next stage runs. The full stage table lives in
[`AGENTS.md`](AGENTS.md) §3.

## Status

**Seed.** This repo bootstraps the methodology, templates, agent guides, a
worked example ([`features/UC-00-login/`](features/UC-00-login/README.md))
taken end-to-end as the canonical example, and an optional runnable Java
reference profile under [`reference-impl/java-micronaut-jena/`](reference-impl/java-micronaut-jena/).
The broader reference implementation lives at
[abratto/tastetag](https://github.com/abratto/tastetag) and will be ported
into `reference-impl/` over subsequent PRs.

Important for template users: `reference-impl/` is a seeded **reference
source**, not the main application root for your downstream product. If
you adopt a profile from this repo, copy the chosen profile's starter
code and patterns into your own project root or runtime folder
(`app/`, `backend/`, `services/api/`, etc.) and set your real package
and source roots in
[`templates/feature-skeleton/_config/package-and-layout.md`](templates/feature-skeleton/_config/package-and-layout.md).
Do not keep extending `reference-impl/` in place with product-specific
code.

## Where this comes from

CLAD did not start as a methodology paper. It started as an experiment —
*does LLM/agentic development actually move the needle, or is the speed
illusory once you account for rework?* — and it was extracted,
generalised, and re-licensed only after it had survived contact with
real code.

### Origins — the bet

The starting position was a thesis, not a project. If LLM/agentic
development is going to become a dominant way to build software, then
the **architecture itself** has to be optimised for the agent, not just
for the human. Concretely that means:

- a **small context window** is enough to understand any one part of
  the system,
- **isolated components** localise the blast radius of any change,
- **declarative orchestration rules** can be read and reasoned about
  without tracing call graphs, and
- **system state is legible** — what you read in the spec is what the
  running system does.

The WYSIWID paper (Meng & Jackson, MIT CSAIL, *Onward!* 2025) was an
immediate match for those properties. The next question was whether a
non-trivial system could actually be built on it with an LLM partner.
[abratto/tastetag](https://github.com/abratto/tastetag) — a
Java/Micronaut/Jena backend with multi-domain taste matching — was
chosen as the test bed precisely because it is non-trivial: real
state, real coordination across concepts, real domain modelling.

The architecture answered "what to build toward." It did not answer
"how to drive the LLM there without losing control." That gap became
the methodology. As implementation progressed, two things became
clear:

1. Several long-standing artefacts of requirements engineering and
   system modelling — Cockburn use cases, state machines, activity
   diagrams, and especially **ORM** (whose binary fact types map
   mechanically to RDF triples and therefore to Legible's
   concept-state graphs) — could be used to capture human intent in a
   form that drives the architecture *directly*, rather than being
   translated by hand.
2. Process and design artefacts that the industry had written off as
   **heavyweight** — RUP-style phase gates, UML, fully-dressed use
   cases — turned out to be extremely valuable *and*, with an LLM
   doing the typing, cheap to produce. Their cost had always been
   transcription and maintenance; once both collapse, what's left is
   the rigour, which is exactly what an agent needs to stay correct.
   The "heavyweight" label was an artefact of the all-human cost
   model, not of the artefacts themselves.

CLAD is the loop that fell out of doing that work: contracts at every
gate, formal artefacts the LLM can consume verbatim, and a rejection
protocol that keeps rework predictable.

One thing did not work: simply *telling* the agent to follow CLAD.
Throughout early Tastetag development the agent had to be re-prompted
constantly to re-read the methodology docs and stay on the process.
Discovering ICM (Van Clief, 2026) was accidental and decisive — its
numbered-stage workspace, with a `CONTEXT.md` contract per stage and
an `output/` folder per stage, is a **structural constraint** that
makes the workflow self-enforcing. The agent reads the contract for
the stage it is standing in; it cannot drift into the next stage
without opening a different folder. ICM was added to CLAD for that
single reason: it converts process discipline from a thing you
remind the agent about into a thing the file system enforces.

Over ~33 calendar days Tastetag's Block 1 shipped 15 concepts, 300+
syncs, 7 domain ontologies, and ~1,100 passing tests with **zero
cross-concept imports**. The bet — that you can move dramatically
faster *and* keep strong correctness guarantees *and* end up with a
well-structured, maintainable system — held. By the close of Block 1
the methodology had stabilised enough to be extracted into this
repository as a starter that anyone can clone.

### Influences

CLAD synthesises three external bodies of work and cites them at every
boundary. None is adopted whole; each contributes a specific load-bearing
piece.

- **WYSIWID — Meng & Jackson, "What You See Is What It Does"** (Onward!
  2025). Source of the runtime architecture: concepts as isolated state
  machines with explicit operational principles, synchronizations as the
  *only* legal coordination primitive, and a single bootstrap concept
  that owns the HTTP surface. CLAD's hard rules R1–R5 are the
  enforceable contract version of the WYSIWID pattern. See
  [methodology/architecture/](methodology/architecture/).

- **ICM — Van Clief, "Interpretable Context Methodology"** (2026).
  Source of the workspace shape: the five-layer context hierarchy,
  numbered-stage feature folders (`stages/NN_*/`), and the
  `CONTEXT.md` stage contract with its `Inputs / Process / Outputs`
  triplet. ICM is what lets a human walk a feature stage by stage with
  the agent stopping at every gate. See
  [methodology/implementation/STAGES.md](methodology/implementation/STAGES.md).

- **ORM / CSDP — Halpin & Jarrar.** Source of the discipline that the
  conceptual schema is decided *before* code, not derived from it. CLAD
  borrows the shape of the CSDP for Stage 03b conceptual data modeling,
  then maps that approved model into a chosen profile at Stage 04a. See
  [methodology/architecture/DATA_MODEL_NOTES.md](methodology/architecture/DATA_MODEL_NOTES.md)
  and [methodology/implementation/STORAGE_MAPPING.md](methodology/implementation/STORAGE_MAPPING.md).

Background traditions that shaped the gate protocol — Cockburn use
cases, Extreme Programming's red-before-green TDD, RUP's artefact-chain
phasing — are noted in
[methodology/reference/CITATIONS.md](methodology/reference/CITATIONS.md).

### What CLAD adds

WYSIWID specifies a runtime pattern. ICM specifies a workspace shape.
Neither tells you *how to drive an LLM through a change* without losing
control. CLAD is the missing piece:

- **Contracts at every stage gate.** Each `stages/NN_*/CONTEXT.md`
  declares exactly what the agent may read, what it must produce, and
  where it must stop. The agent does not advance until the human has
  inspected `output/`. This is what keeps generation speed inside a
  pre-validated scope rather than ahead of it.
- **Hard rules that CI enforces.** "No concept imports another concept"
  is not a guideline — it is a job (`hard-rule-r1`) that fails the
  build. Architecture drift is a defect class CLAD makes structurally
  impossible, not merely discouraged.
- **A rejection protocol** ([AGENTS.md](AGENTS.md) §6). When the human
  pushes back, the agent re-runs the same stage with one targeted
  question — it does not freelance, drop back, or silently advance.
  This is the single biggest difference between productive and
  exhausting LLM rework.
- **Deterministic cross-stage verification scripts.** CLAD ships a suite
  of profile-agnostic Python scripts under [`quality-gate/`](quality-gate/)
  that automate the cross-stage consistency checks previously done by LLM
  self-audit. Each script replaces a non-deterministic "did the LLM
  remember to check this?" step with a pass/fail command. Checks include
  file manifest integrity ([`verify_file_manifest.py`](quality-gate/verify_file_manifest.py)),
  scenario coverage ([`verify_scenario_coverage.py`](quality-gate/verify_scenario_coverage.py)),
  outcome alignment ([`verify_outcome_alignment.py`](quality-gate/verify_outcome_alignment.py)),
  action chain consistency ([`verify_action_chain.py`](quality-gate/verify_action_chain.py)),
  sync contract matrix completeness ([`verify_sync_matrix.py`](quality-gate/verify_sync_matrix.py)),
  CSDP data-model structure ([`verify_data_model.py`](quality-gate/verify_data_model.py)),
  and SPEC parity ([`verify_spec_parity.py`](quality-gate/verify_spec_parity.py)).
  See [`methodology/implementation/QUALITY_GATE.md`](methodology/implementation/QUALITY_GATE.md).
- **Outer-loop BDD tests (optional Gherkin/Cucumber track).** Stage 04c
  can mechanically derive executable Gherkin `.feature` files and
  step-definition skeletons from the use case, chain tables, and SPECs,
  replacing hand-written markdown flow specs with executable
  specifications that go green at the end of 04e. Chosen per-feature via
  `_config/test-framework.md`. See
  [methodology/architecture/GHERKIN_INTEGRATION.md](methodology/architecture/GHERKIN_INTEGRATION.md).
- **Optional overlays, not mandates.** Tracking
  ([methodology/overlays/TRACKING.md](methodology/overlays/TRACKING.md))
  and planning intake
  ([methodology/overlays/PLANNING.md](methodology/overlays/PLANNING.md))
  and decision logs
  ([methodology/overlays/DECISIONS.md](methodology/overlays/DECISIONS.md))
  are bolt-ons; the core loop works without either.

The proposed benefit is not "ship faster." It is **ship under review at
LLM speed without losing the audit trail.** Every stage produces a file
you can diff, every action emits a flow token you can trace, every
hard rule is checked by CI. The methodology amplifies one careful
human's judgment rather than replacing it.

## Quick start

> **Using this as a starter for your own project?** Click **"Use this
> template"** at the top of the GitHub repo (or
> [follow this link](https://github.com/abratto/clad/generate)) to get
> a clean copy with no fork relationship — then read on.

When you later implement against a concrete profile, treat
`reference-impl/` as upstream example material. Your real application
code should live under your own chosen project root, not inside the
starter's `reference-impl/` tree.

```bash
git clone https://github.com/abratto/clad.git
cd clad
# Read in this order:
#   1. README.md (you are here)
#   2. AGENTS.md                       ← canonical guide for any AI coding agent
#   3. methodology/README.md           ← reading order for the methodology
#   4. methodology/WALKTHROUGH.md      ← annotated UC-00 session, turn by turn
#   5. features/UC-00-login/README.md  ← the worked example itself
```

### Your first prompt — load the methodology

After cloning, open a chat with your agent (Copilot, Claude, Cursor,
Codex, …) in this workspace and send exactly this:

> Read `AGENTS.md` in full, then `CONTEXT.md`, then
> `methodology/README.md`, then `methodology/WALKTHROUGH.md`. Confirm you
> understand the five-layer hierarchy and the stage flow, then wait for
> my next instruction.

That loads the binding rules (`AGENTS.md`), the workspace router
(`CONTEXT.md`), the methodology reading order, and an annotated example
of what a single CLAD turn looks like — without pulling in any
feature-specific material the agent shouldn't have yet.

### Your second prompt — start Stage 00

> Open `features/_system/stages/00_actor-goal/CONTEXT.md` and read it.
> Then run Stage 00 against this brief: *<one paragraph describing what
> you want the system to let users do>*. Ask up to five clarifying
> questions in one turn; after I answer and approve, write the final
> artefacts to `features/_system/stages/00_actor-goal/output/actors.md`
> and `features/_system/stages/00_actor-goal/output/goals.md`.

The agent will run **Stage 00 (actor/goal)** at system scope: it
proposes a draft actor list and goal list, asks up to five clarifying
questions, and **waits for your answers** before writing the approved
artefacts.

### After Stage 00 passes

Once `features/_system/stages/00_actor-goal/output/goals.md` is approved,
tell the agent to proceed. The next action is mechanical and should be
performed by the agent: create one UC folder per in-scope goal by
copying the feature skeleton, then open Stage 01 in the first UC folder.

```bash
# agent action, not required manual shell work:
cp -R templates/feature-skeleton features/UC-01-<slug>
# repeat for each remaining in-scope goal with the next UC number
# then open:
#   features/UC-01-<slug>/stages/01_usecase/CONTEXT.md
```

The human responsibility here is the gate: approve Stage 00 or send it
back for correction. Once approved, the agent should continue the flow
by creating the UC folders and moving into Stage 01 unless the human
explicitly wants to pause.

If you plan to adopt the Java reference profile, read
[`reference-impl/java-micronaut-jena/README.md`](reference-impl/java-micronaut-jena/README.md)
after Stage 00 passes and before Stage 04 implementation work. That file
shows how to copy the starter profile into your real app root, how to run
it locally, and how the Java package/source-root conventions map back into
`_config/package-and-layout.md`. The Java profile also ships a Cucumber
integration for the Gherkin track — set `TEST_FRAMEWORK=CUCUMBER` in
`_config/test-framework.md` to use it (see
[methodology/architecture/GHERKIN_INTEGRATION.md](methodology/architecture/GHERKIN_INTEGRATION.md)).

If you want to sequence multiple goals before implementation, adopt the
optional planning overlay:

- [methodology/overlays/PLANNING.md](methodology/overlays/PLANNING.md)
- [templates/plan-board.md](templates/plan-board.md)

### Cline setup (optional — local agentic loop)

If you are using [Cline](https://docs.cline.bot/) in VS Code, CLAD now
ships workspace rules under `.clinerules/` that preserve the old
Roo-mode workflow as closely as Cline allows. Cline already reads
`AGENTS.md`; the additional rule files let you manually toggle the
current CLAD phase:

- `10-clad-architect.md` for Stages `00`-`03` and `05`
- `20-clad-red.md` for red test/spec work in `04c`-`04e`
- `30-clad-green.md` for green implementation after explicit approval

Enable exactly one of those phase rules at a time in the Cline Rules
panel.

The underlying CLAD process prompt does **not** change across local
agent frameworks. `AGENTS.md` remains the canonical instruction source
for Copilot, Cline, Roo, Cursor, and other agents. What changes by tool
is only the local wiring:

- Roo used custom modes and mode-specific rule files.
- Cline uses Plan/Act plus `.clinerules/` toggles.
- Copilot uses repository instructions plus normal tool permissions.

In other words: when someone clones this repo from the template, they
should not need a different CLAD methodology prompt just because they
prefer Cline over Roo. The process contract is shared; the shell around
it is tool-specific.

#### Manual Cline settings

Set these locally in Cline before long CLAD sessions:

- Enable **Auto Compact**.
- If you prefer different models for planning and implementation,
  enable **Use different models for Plan and Act**.
- Keep the CLAD phase rules visible in the Rules panel and toggle only
  one of `10-clad-architect.md`, `20-clad-red.md`, or
  `30-clad-green.md` at a time.

Important: current Cline documentation describes Auto Compact as a
feature, but does **not** document a portable repo-committed settings
file for an Auto Compact threshold or custom compaction prompt. Because
of that, CLAD does not commit a fake `.cline/` settings file for those
values. Auto Compact behavior is currently a **per-user Cline setting**,
not a team-shared repository config.

Plan/Act and CLAD phase are **orthogonal**:

- `Plan` means read/search/discuss only.
- `Act` means Cline may edit files and run commands.
- `10-clad-architect.md` / `20-clad-red.md` / `30-clad-green.md`
  decide **what kind of work** CLAD allows.

Typical CLAD-on-Cline combinations:

- `Plan` + `10-clad-architect.md`: inspect stage context, review artefacts, plan the stage.
- `Act` + `10-clad-architect.md`: write Stage `00`-`03` or `05` artefacts.
- `Act` + `20-clad-red.md`: write Stage `04` red tests/specs.
- `Act` + `30-clad-green.md`: implement approved Stage `04` work.

One manual step is required before Stage `04` implementation work:

```bash
cp .cline-clad-config.example .cline-clad-config
```

Then open `.cline-clad-config` and fill in two values for your project:

```
TEST_COMMAND=mvn -f reference-impl/java-micronaut-jena/pom.xml test
STORAGE_LAYER=Jena TDB2 named graph (Java/Micronaut profile)
```

`.cline-clad-config` is gitignored — it is yours alone and will not be
committed. See [`.cline-clad-config.example`](.cline-clad-config.example)
for examples covering Maven, Gradle, npm, and common storage profiles.

That file is **not** where Auto Compact settings live. It exists only
for CLAD implementation-time inputs such as the test command and the
storage profile.

Cline will detect `.clinerules/` and `AGENTS.md` automatically on
workspace open. Use `.clineignore` to keep generated/build files out of
automatic context gathering.

Limitation versus Roo: Cline rules do not enforce Roo-style `fileRegex`
edit fences. The phase boundaries are preserved as rule instructions,
not as hard tool-level write restrictions.

## Repository layout

```
clad/
├── README.md
├── LICENSE                          Apache-2.0
├── NOTICE                           Third-party attributions
├── SECURITY.md                      Vulnerability reporting policy
├── CHANGELOG.md                     Per-version changes
├── ROADMAP.md                       Optional tracking overlay (CI-checked)
├── CONTRIBUTING.md
├── AGENTS.md                        Canonical agent guide (single source)
├── CLAUDE.md                        Adapter -> AGENTS.md
├── .github/copilot-instructions.md  Adapter -> AGENTS.md
├── .cursor/rules/clad.mdc           Adapter -> AGENTS.md
├── .clinerules/                     Cline workspace rules for CLAD phases
├── .clineignore                     Cline automatic-context exclusions
├── .cline-clad-config.example       Template for per-developer Cline config
├── CONTEXT.md                       Workspace routing (ICM Layer 1)
├── .roomodes                        Legacy Roo custom modes
├── .roo-clad-config.example         Legacy Roo per-developer config
│
├── methodology/
│   ├── README.md                    Reading order
│   ├── WALKTHROUGH.md               Annotated UC-00 session (turn by turn)
│   ├── core/                        CLAD: contracts, artefacts, principles
│   ├── architecture/                Legible/WYSIWID + ARTEFACT_MAP.md
│   ├── implementation/              Hard rules + ICM stage mapping
│   ├── overlays/                    Optional: tracking, planning, decision logs
│   └── reference/                   Citations and source pointers
│
├── templates/                       Per-artefact templates +
│   ├── feature.feature              Gherkin feature file (Cucumber/BDD track)
│   ├── step-definitions.java        Step-definition skeleton (Cucumber/BDD track)
│   ├── plan-board.md                Optional sequencing board for overlays/PLANNING
│   └── feature-skeleton/            ...empty stage tree to copy for new features
│
├── features/
│   ├── README.md
│   ├── _system/                     System-level Stage 00 (actors.md, goals.md)
│   │   └── stages/00_actor-goal/    Run once per project brief
│   └── UC-00-login/                 Worked example (read, do not copy)
│       ├── README.md                Stage-by-stage index with rationale
│       ├── _config/                 Feature-scoped reference (Layer 3)
│       └── stages/
│           ├── 00_actor-goal/
│           ├── 01_usecase/
│           ├── 02a_responsibility-map/
│           ├── 02b_chain-table/
│           ├── 02_concepts/
│           ├── 03_syncs/
│           ├── 03a_dependency-review/
│           ├── 03b_data-model/
│           ├── 04_implement/        Router + 04a_storage-mapping, 04b_spec,
│           │                        04c_flow-tests, 04d_concept-tdd
│           │                        (04d_red-tests, 04d_green-impl),
│           │                        04e_sync-tdd (04e_red-tests,
│           │                        04e_green-impl)
│           └── 05_verify/
│
└── reference-impl/
    └── java-micronaut-jena/         Optional Java profile (skeleton)
```

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

## Citations

- Meng, E. & Jackson, D. (2025). *What You See Is What It Does: A Structural
  Pattern for Legible Software.* Onward! 2025.
  [DOI 10.1145/3759429.3762628](https://doi.org/10.1145/3759429.3762628) ·
  [arXiv 2508.14511](https://arxiv.org/abs/2508.14511)
- Van Clief, J. (2026). *Interpretable Context Methodology (ICM).*
  [arXiv 2603.16021](https://arxiv.org/abs/2603.16021) ·
  [github.com/RinDig/Interpretable-Context-Methodology-ICM-](https://github.com/RinDig/Interpretable-Context-Methodology-ICM-)
