# methodology/ — reading order

This folder is the stable reference material (ICM Layer 3) for the CLAD
discipline. Read it in this order:

## 1. Core — what CLAD is

1. [`core/CLAD.md`](core/CLAD.md) — principles and the contract loop
2. [`core/CONTRACTS.md`](core/CONTRACTS.md) — what counts as a contract
3. [`core/ARTEFACTS.md`](core/ARTEFACTS.md) — what counts as an artefact
4. [`core/ITERATIVE_CHANGES.md`](core/ITERATIVE_CHANGES.md) — when not to re-run 00→05

## 2. Architecture — how the running system is structured

These files describe the **Legible architecture (WYSIWID pattern)** that
CLAD targets. They are paraphrases of, and citations to, Meng & Jackson
(2025); see [`reference/CITATIONS.md`](reference/CITATIONS.md).

1. [`architecture/LEGIBLE.md`](architecture/LEGIBLE.md) — the WYSIWID idea
2. [`architecture/CONCEPTS.md`](architecture/CONCEPTS.md) — concept anatomy
3. [`architecture/SYNCHRONIZATIONS.md`](architecture/SYNCHRONIZATIONS.md) — sync semantics
4. [`architecture/FLOW_TOKENS.md`](architecture/FLOW_TOKENS.md) — provenance and back-tracing
5. [`architecture/ENGINE.md`](architecture/ENGINE.md) — the runtime engine that the Java reference profile implements
6. [`architecture/WEB_CONCEPT.md`](architecture/WEB_CONCEPT.md) — the bootstrap `Web` concept (R4)
7. [`architecture/ORM_NOTES.md`](architecture/ORM_NOTES.md) — drafting per-concept state schemas (Stage 04a)

## 3. Implementation — hard rules and the workspace scaffold

1. [`implementation/RULES.md`](implementation/RULES.md) — the non-negotiable rules
2. [`implementation/STAGES.md`](implementation/STAGES.md) — how CLAD stages map onto the ICM scaffold
3. [`implementation/QUALITY_GATE.md`](implementation/QUALITY_GATE.md) — pre-commit checks per profile

## 4. Reference

1. [`reference/CITATIONS.md`](reference/CITATIONS.md) — sources and attributions

## 5. Optional overlays

These are **not** part of the canonical reading order. Adopt them only
if the corresponding pain shows up in your workflow.

1. [`overlays/TRACKING.md`](overlays/TRACKING.md) — one-active-feature
   discipline, ROADMAP convention, session start/resume checklists,
   issue/PR labels.
2. [`overlays/DECISIONS.md`](overlays/DECISIONS.md) — append-only ADR
   trail for cross-cutting choices.
