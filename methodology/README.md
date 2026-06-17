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
2. [`architecture/MENTAL_MODEL.md`](architecture/MENTAL_MODEL.md) — OO ↔ WYSIWID parallel and the complete artefact map (start here if you come from OO)
3. [`architecture/CONCEPTS.md`](architecture/CONCEPTS.md) — concept anatomy
4. [`architecture/SYNCHRONIZATIONS.md`](architecture/SYNCHRONIZATIONS.md) — sync semantics
5. [`architecture/SYNC_PATTERNS.md`](architecture/SYNC_PATTERNS.md) — the four legal data-flow patterns (A/B/C/D)
6. [`architecture/FLOW_TOKENS.md`](architecture/FLOW_TOKENS.md) — provenance and back-tracing
7. [`architecture/ENGINE.md`](architecture/ENGINE.md) — the runtime engine that the Java reference profile implements
8. [`architecture/WEB_CONCEPT.md`](architecture/WEB_CONCEPT.md) — the bootstrap `Web` concept (R4)
9. [`architecture/DATA_MODEL_NOTES.md`](architecture/DATA_MODEL_NOTES.md) — drafting per-concept conceptual data models (Stage 03b)
10. [`architecture/ARTEFACT_MAP.md`](architecture/ARTEFACT_MAP.md) — the dependency graph between every per-feature artefact (producer → consumer, with the data each consumer needs and why)
11. [`architecture/GHERKIN_INTEGRATION.md`](architecture/GHERKIN_INTEGRATION.md) — the optional Gherkin/Cucumber outer-red BDD track (derivation rules, cross-stage consistency, worked example)

## 3. Implementation — hard rules and the workspace scaffold

1. [`implementation/RULES.md`](implementation/RULES.md) — the non-negotiable rules
2. [`implementation/STAGES.md`](implementation/STAGES.md) — how CLAD stages map onto the ICM scaffold
3. [`implementation/STORAGE_MAPPING.md`](implementation/STORAGE_MAPPING.md) — mapping conceptual data models onto a concrete profile (Stage 04a)
4. [`implementation/QUALITY_GATE.md`](implementation/QUALITY_GATE.md) — local pre-commit checks per profile
5. [`implementation/DELIVERY.md`](implementation/DELIVERY.md) — trunk-based delivery posture, CI gate, branch protection

## 4. Reference

1. [`reference/CITATIONS.md`](reference/CITATIONS.md) — sources and attributions

## 5. Worked example — how a CLAD session actually runs

- [`WALKTHROUGH.md`](WALKTHROUGH.md) — turn-by-turn replay of producing UC-00-login from brief through Stage 05, with the loaded `CONTEXT.md`, opened inputs, written outputs, and gate question called out at every turn. Read this alongside [`../features/UC-00-login/README.md`](../features/UC-00-login/README.md).

## 6. Optional overlays

These are **not** part of the canonical reading order. Adopt them only
if the corresponding pain shows up in your workflow.

1. [`overlays/TRACKING.md`](overlays/TRACKING.md) — one-active-feature
   discipline, ROADMAP convention, session start/resume checklists,
   issue/PR labels.
2. [`overlays/PLANNING.md`](overlays/PLANNING.md) — intake and sequencing
   overlay for deciding what to start next before Stage 00.
3. [`overlays/DECISIONS.md`](overlays/DECISIONS.md) — append-only ADR
   trail for cross-cutting choices.
4. [`overlays/LOCAL_LLM.md`](overlays/LOCAL_LLM.md) — context-window
   discipline for local model runs (Cline Auto Compact + `RESUME.md`
   working-memory loop).
