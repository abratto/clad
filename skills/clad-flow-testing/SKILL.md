---
name: clad-flow-testing
description: Write outer-red flow tests during CLAD Stage 04c. Use when producing Gherkin .feature files, step-definition skeletons, and stub flow tests from approved use cases and chain tables under the London School TDD double-loop.
---

# CLAD Flow Testing (Stage 04c)

> **Role:** required stage guidance for Stage 04c. The stage `CONTEXT.md` `Inputs` table is authoritative for *which files to load*; load those exactly. This skill adds working process only and must not cause you to reload documents the contract already named.

## What this skill covers

Writing the outer-red flow tests — Gherkin `.feature` files and
step-definition skeletons for each use-case scenario. This is Gate 3
(Executable specification) — the last human gate before implementation.

## Files

Stage 04c `Inputs` names `TDD.md`, the `.feature`/step-def/flow templates, `FLOW_TOKENS.md`, and the 01/01b/04b outputs. The extra `methodology/architecture/GHERKIN_INTEGRATION.md` derivation rules (G1–G5, S1–S3, E1) is the only reference worth having open alongside `Inputs`.

## Process

1. Derive one Gherkin `.feature` per use-case scenario from
   `01_usecase` + `01b_chain-table` + `04b_spec`.
2. Derive step-definition skeletons from chain-table rows and SPEC
   outcome enums.
3. If `port-spec.md` exists, add at least one `@contract` scenario per
   HTTP endpoint. Assert exact JSON paths, constrained field types, and
   the primary error envelope shape.
4. Produce per-scenario markdown flow specs and stub flow test files.
5. Self-audit: run `python3 quality-gate/verify_artefacts.py` and fix any defects.
6. Stop at the gate (Gate 3 — human reviews the executable specification).

## Hard constraints

- `.feature` files are derived views — regenerate when the use case
  changes, do not hand-edit.
- `04b_spec` must exist before `04c` begins.
- Markdown alone does not complete the stage; stub flow tests must exist.
- When a port spec exists, `@contract` scenarios are required and must
   use exact JSON path/type/envelope assertions rather than string-contains.
- Do not merge `04c`, `04d`, and `04e` into one pass.
