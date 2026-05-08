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
taken end-to-end through Stage 04 (the LoginFlowTest is currently
`@Disabled` pending Stage 05 closure), and an optional Java reference
profile under [`reference-impl/java-micronaut-jena/`](reference-impl/java-micronaut-jena/).
The broader reference implementation lives at
[abratto/tastetag](https://github.com/abratto/tastetag) and will be ported
into `reference-impl/` over subsequent PRs.

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
  borrows the *shape* of the seven-step CSDP for per-concept schemas —
  not the full ORM-ML notation. See
  [methodology/architecture/ORM_NOTES.md](methodology/architecture/ORM_NOTES.md).

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
- **Optional overlays, not mandates.** Tracking
  ([methodology/overlays/TRACKING.md](methodology/overlays/TRACKING.md))
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
├── CONTEXT.md                       Workspace routing (ICM Layer 1)
│
├── methodology/
│   ├── README.md                    Reading order
│   ├── WALKTHROUGH.md               Annotated UC-00 session (turn by turn)
│   ├── core/                        CLAD: contracts, artefacts, principles
│   ├── architecture/                Legible/WYSIWID + ARTEFACT_MAP.md
│   ├── implementation/              Hard rules + ICM stage mapping
│   ├── overlays/                    Optional: tracking, decision logs
│   └── reference/                   Citations and source pointers
│
├── templates/                       Per-artefact templates +
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
│           ├── 04_implement/        Router + 04a_orm, 04b_spec,
│           │                        04c_flow-tests, 04d_concept-tdd, 04e_sync-tdd
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
