---
name: clad-verification
description: Verify and trace running behaviour during CLAD Stage 05. Use when back-tracing runtime flow tokens to use case scenarios, producing trace reports, smoke testing, and closing a feature.
---

# CLAD Verification (Stage 05)

> **Role:** required stage guidance for Stage 05. The stage `CONTEXT.md` `Inputs` table is authoritative for *which files to load*; load those exactly. This skill adds working process only and must not cause you to reload documents the contract already named.

## What this skill covers

Closing a feature: back-tracing runtime flow tokens to use-case scenarios,
smoke testing the deployable artefact, and recording findings. Every
scenario gets a status: covered, partial, or missing.

## Files

Stage 05 `Inputs` names `FLOW_TOKENS.md`, the 01 use case, and the runtime evidence. The extra `01b_chain-table/output/` (expected action sequences) supports the back-trace.

## Process

1. Trace from runtime flow tokens back to `usecase.md` scenarios.
2. Mark each scenario: covered, partial, or missing.
3. Smoke the deployable artefact.
4. Produce `output/trace.md`, `output/findings.md`,
   `output/smoke.md`, `output/tracking.md`.
5. Self-audit: run `python3 quality-gate/verify_artefacts.py` and fix any defects.
6. Auto-close the feature.

## Hard constraints

- Every observable effect must back-trace to a use case (R7).
- Do not close with any scenario at "missing" without explicit human sign-off.
- Every scenario must have a status.
