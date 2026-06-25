---
name: clad-verification
description: Verify and trace running behaviour during CLAD Stage 05. Use when back-tracing runtime flow tokens to use case scenarios, producing trace reports, smoke testing, and closing a feature.
---

# CLAD Verification (Stage 05)

## What this skill covers

Closing a feature: back-tracing runtime flow tokens to use-case scenarios,
smoke testing the deployable artefact, and recording findings. Every
scenario gets a status: covered, partial, or missing.

## Quick reference

Load these files:

1. `methodology/architecture/FLOW_TOKENS.md` — token structure for trace
2. `features/UC-XX-<slug>/stages/01_usecase/output/usecase.md` —
   use case scenarios to trace against
3. `features/UC-XX-<slug>/stages/02b_chain-table/output/` —
   approved chain tables for expected action sequences
4. The running system (for live token inspection)
5. The current stage `CONTEXT.md` for exact Inputs/Outputs/Process

## Process

1. Trace from runtime flow tokens back to `usecase.md` scenarios.
2. Mark each scenario: covered, partial, or missing.
3. Smoke the deployable artefact.
4. Produce `output/trace.md`, `output/findings.md`,
   `output/smoke.md`, `output/tracking.md`.
5. Auto-close the feature.

## Hard constraints

- Every observable effect must back-trace to a use case (R7).
- Do not close with any scenario at "missing" without explicit human sign-off.
- Every scenario must have a status.
