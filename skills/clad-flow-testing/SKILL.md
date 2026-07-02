---
name: clad-flow-testing
description: Write outer-red flow tests during CLAD Stage 04c. Use when producing Gherkin .feature files, step-definition skeletons, and stub flow tests from approved use cases and chain tables under the London School TDD double-loop.
---

# CLAD Flow Testing (Stage 04c)

## What this skill covers

Writing the outer-red flow tests — Gherkin `.feature` files and
step-definition skeletons for each use-case scenario. This is Gate 3
(Executable specification) — the last human gate before implementation.

## Quick reference

Load these files:

1. `methodology/implementation/TDD.md` — London School outside-in
   double-loop discipline
2. `methodology/architecture/GHERKIN_INTEGRATION.md` — derivation rules
   G1-G5 (Gherkin), S1-S3 (step definitions), E1 (evidence)
3. `templates/feature.feature` — Gherkin `.feature` template with
   embedded derivation rules
4. `templates/step-definitions.java` — Cucumber step-definition skeleton
5. `templates/flow.md` — flow test spec template
6. `methodology/architecture/FLOW_TOKENS.md` — token structure
7. `features/UC-XX-<slug>/stages/01_usecase/output/usecase.md` —
   source scenarios
8. `features/UC-XX-<slug>/stages/02b_chain-table/output/` —
   approved chain tables
9. `features/UC-XX-<slug>/stages/04b_spec/output/` —
   SPEC slices to compile against
10. The current stage `CONTEXT.md` for exact Inputs/Outputs/Process
11. `features/_system/stages/00_actor-goal/output/port-spec.md` — only
   when it exists; external adapter contract for `@contract` scenarios

## Process

1. Derive one Gherkin `.feature` per use-case scenario from
   `01_usecase` + `02b_chain-table` + `04b_spec`.
2. Derive step-definition skeletons from chain-table rows and SPEC
   outcome enums.
3. If `port-spec.md` exists, add at least one `@contract` scenario per
   HTTP endpoint. Assert exact JSON paths, constrained field types, and
   the primary error envelope shape.
4. Produce per-scenario markdown flow specs and stub flow test files.
5. Stop at the gate (Gate 3 — human reviews the executable specification).

## Hard constraints

- `.feature` files are derived views — regenerate when the use case
  changes, do not hand-edit.
- `04b_spec` must exist before `04c` begins.
- Markdown alone does not complete the stage; stub flow tests must exist.
- When a port spec exists, `@contract` scenarios are required and must
   use exact JSON path/type/envelope assertions rather than string-contains.
- Do not merge `04c`, `04d`, and `04e` into one pass.
