# Where this comes from

CLAD did not start as a methodology paper. It started as an experiment —
*does LLM/agentic development actually move the needle, or is the speed
illusory once you account for rework?* — and it was extracted,
generalised, and re-licensed only after it had survived contact with
real code.

## Origins — the bet

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
A private Java/Micronaut/Jena backend called Tastetag was chosen as the
test bed precisely because it is non-trivial: real state, real
coordination across concepts, real domain modelling.

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

## Influences

CLAD synthesises three external bodies of work and cites them at every
boundary. None is adopted whole; each contributes a specific load-bearing
piece.

- **WYSIWID — Meng & Jackson, "What You See Is What It Does"** (Onward!
  2025). Source of the runtime architecture: concepts as isolated state
  machines with explicit operational principles, synchronizations as the
  *only* legal coordination primitive, and a single bootstrap concept
  that owns the HTTP surface. CLAD's hard rules R1–R5 are the
  enforceable contract version of the WYSIWID pattern. See
  [methodology/architecture/](../methodology/architecture/).

- **ICM — Van Clief, "Interpretable Context Methodology"** (2026).
  Source of the workspace shape: the five-layer context hierarchy,
  numbered-stage feature folders (`stages/NN_*/`), and the
  `CONTEXT.md` stage contract with its `Inputs / Process / Outputs`
  triplet. ICM is what lets a human walk a feature stage by stage with
  the agent stopping at every gate. See
  [methodology/implementation/STAGES.md](../methodology/implementation/STAGES.md).

- **ORM / CSDP — Halpin & Jarrar.** Source of the discipline that the
  conceptual schema is decided *before* code, not derived from it. CLAD
  borrows the shape of the CSDP for Stage 03b conceptual data modeling,
  then maps that approved model into a chosen profile at Stage 04a. See
  [methodology/architecture/DATA_MODEL_NOTES.md](../methodology/architecture/DATA_MODEL_NOTES.md)
  and [methodology/implementation/STORAGE_MAPPING.md](../methodology/implementation/STORAGE_MAPPING.md).

Background traditions that shaped the gate protocol — Cockburn use
cases, Extreme Programming's red-before-green TDD, RUP's artefact-chain
phasing — are noted in
[methodology/reference/CITATIONS.md](../methodology/reference/CITATIONS.md).

## What CLAD adds

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
- **A rejection protocol** ([AGENTS.md](../AGENTS.md) §6). When the human
  pushes back, the agent re-runs the same stage with one targeted
  question — it does not freelance, drop back, or silently advance.
  This is the single biggest difference between productive and
  exhausting LLM rework.
- **Deterministic cross-stage verification scripts.** CLAD ships a suite
  of profile-agnostic Python scripts under [`quality-gate/`](../quality-gate/)
  that automate the cross-stage consistency checks previously done by LLM
  self-audit. Each script replaces a non-deterministic "did the LLM
  remember to check this?" step with a pass/fail command. Checks include
  file manifest integrity ([`verify_file_manifest.py`](../quality-gate/verify_file_manifest.py)),
  scenario coverage ([`verify_scenario_coverage.py`](../quality-gate/verify_scenario_coverage.py)),
  outcome alignment ([`verify_outcome_alignment.py`](../quality-gate/verify_outcome_alignment.py)),
  action chain consistency ([`verify_action_chain.py`](../quality-gate/verify_action_chain.py)),
  sync contract matrix completeness ([`verify_sync_matrix.py`](../quality-gate/verify_sync_matrix.py)),
  CSDP data-model structure ([`verify_data_model.py`](../quality-gate/verify_data_model.py)),
  and SPEC parity ([`verify_spec_parity.py`](../quality-gate/verify_spec_parity.py)).
  See [`methodology/implementation/QUALITY_GATE.md`](../methodology/implementation/QUALITY_GATE.md).
- **Outer-loop BDD tests (Cucumber/Gherkin).** Stage 04c
  derives executable Gherkin `.feature` files and step-definition
  skeletons from the use case, chain tables, and SPECs, replacing
  hand-written markdown flow specs with executable specifications
  that go green at the end of 04e. See
  [methodology/architecture/GHERKIN_INTEGRATION.md](../methodology/architecture/GHERKIN_INTEGRATION.md).
- **Optional overlays, not mandates.** Tracking
  ([methodology/overlays/TRACKING.md](../methodology/overlays/TRACKING.md))
  and planning intake
  ([methodology/overlays/PLANNING.md](../methodology/overlays/PLANNING.md))
  and decision logs
  ([methodology/overlays/DECISIONS.md](../methodology/overlays/DECISIONS.md))
  are bolt-ons; the core loop works without either.

The proposed benefit is not "ship faster." It is **ship under review at
LLM speed without losing the audit trail.** Every stage produces a file
you can diff, every action emits a flow token you can trace, every
hard rule is checked by CI. The methodology amplifies one careful
human's judgment rather than replacing it.
