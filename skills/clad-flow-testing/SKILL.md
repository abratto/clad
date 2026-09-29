---
name: clad-flow-testing
description: Author the frozen Acceptance Spec and native per-scenario flow tests during CLAD Stage 04c. Use when deriving acceptance-spec.md and native flow-test methods from approved use cases, chain tables, contracts, and sync specs. Gate 3 is the Acceptance spec.
---

# CLAD Flow Testing (Stage 04c)

> **Role:** required stage guidance for Stage 04c. The stage `CONTEXT.md` `Inputs` table is authoritative for *which files to load*; load those exactly. This skill adds working process only and must not cause you to reload documents the contract already named.

## What this skill covers

Writing the frozen, human-facing `output/acceptance-spec.md` (the Gate 3
artifact) plus the **native per-scenario flow tests** that enforce it.
The native test is the executable form of the scenario — there is no
separate BDD feature-file track and no generated glue layer. Read
`methodology/implementation/TESTING.md` before writing anything.

## Files

Stage 04c `Inputs` names `TESTING.md`, `templates/acceptance-spec.md`,
`templates/http-integration-test.java`, `FLOW_TOKENS.md`, and the
01/01b/03/04b outputs. The Acceptance Spec is a derived view — every row
traces to the use case, a chain table, a contract, or a sync spec; it
invents nothing.

## Process

1. Derive one `## Scenario:` section in `acceptance-spec.md` per top-level
   `### Scenario:` in `usecase.md`, using the exact scenario name.
   Record the trigger, expected response (literals from the sync spec's
   `then`), expected token chain (from the chain table), postconditions,
   and one or more `**Test:**` bindings.
2. Write the native per-scenario flow test methods under
   `APP_TEST_SOURCE_ROOT`; each asserts the transport response and the
   runtime flow-token chain. One method per spec binding.
3. If the feature exposes an adapter surface (HTTP/CLI/GraphQL/pub-sub),
   derive a profile-specific end-to-end integration test from
   `templates/http-integration-test.java` (may be `@Disabled` until the
   implementation lands; Stage 05 re-runs it).
4. If `port-spec.md` has inbound entries, add at least one `@contract`
   block per inbound port asserting exact paths, field types, and the
   primary failure envelope.
5. If the response carries a collection, add a `## Collection coverage`
   section naming the empty, multi-item, and (where applicable)
   repeated-key fixtures.
6. Confirm the tests compile with the canonical build/test command.
7. Self-audit: run `python3 quality-gate/verify_artefacts.py` and fix any defects.
8. Stop at the gate (Gate 3 — Acceptance spec; the human reviews
   `usecase.md` + the frozen `acceptance-spec.md`).

## Hard constraints

- The Acceptance Spec is **frozen** at Gate 3: editing it after approval
  stales Gate 3 and forces human re-approval.
- Outcome values are SCREAMING_SNAKE_CASE, copied from the contract;
  token count = number of chain-table rows — no phantom tokens.
- `04b_contract` must exist before `04c` begins.
- Markdown alone does not complete the stage; native flow tests must
  exist and compile.
- When a port spec exists, `@contract` assertions use exact JSON
  path/type/envelope assertions rather than string-contains.
- No password or secret appears in any token payload.
- `verify_acceptance_binding.py` must pass: every use-case scenario has a
  spec section, every `Test:` binding resolves, and every `*FlowTest`
  method is documented.
- Do not merge `04c`, `04d`, and `04e` into one pass.
