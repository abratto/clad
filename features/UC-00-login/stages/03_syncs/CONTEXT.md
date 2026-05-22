# Stage 03 — Synchronizations

## Why this stage exists

Coordination is **declarative** so that **no concept imports another**
(hard rule R1) and so each cross-concept link is reviewable as a small
`when … where … then` rule rather than being buried in imperative
code. Each sync also commits to one of the four legal data-flow
patterns (A/B/C/D), which makes Stage 03a's audit and Stage 04e's TDD
mechanical.

**Feeds:**

- `<name>.sync.md` → 03a (every `then` call and every `where` clause is tabulated; Pattern D reads are flagged), 04c (the sync chain is what the outer flow test asserts), 04e (one inner red→green TDD pass per sync), 05 (the verifier checks that every observed call is authorised by a sync or a use-case scenario).

**Agent stance for this stage:** if you reach for an `if`, you are in
the wrong file. Branching belongs inside a concept action's outcomes;
the sync just says *"when outcome X fires → then call Y."*

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | Scenarios to satisfy |
| `../02_concepts/output/` | 4 | Concepts available to coordinate |
| `../02b_chain-table/output/` | 4 | The action chain each sync formalises |
| `../../../../methodology/architecture/SYNCHRONIZATIONS.md` | 3 | Sync semantics |
| `../../../../methodology/architecture/SYNC_PATTERNS.md` | 3 | The four `where` patterns (A/B/C/D) |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rules (R3) |
| `../../../../templates/sync.md` | 3 | Output template |

## Process

For each scenario in the use case, identify the chain of concept actions
that fulfils it. Each coordination link becomes one sync.

Before writing sync prose, build a per-sync **Sync Contract Matrix** from
the approved chain table and concept files. For each transition, record
the source row id, target row id, exact `when` signature, exact `then`
signature, and any allowed literals. Copy tokens verbatim.

If any action signature, outcome name, argument name, or literal differs
between `../02b_chain-table/output/` and `../02_concepts/output/`, stop
and reopen Stage 02. Stage 03 does not normalize earlier-stage drift.

Syncs are declarative `when … where … then …`; no imperative branching,
no state, no I/O. `where` is data routing only. It may use field-path
references and sync constants, but it may not invent convenience fields.
It is binding-only: no JSON assembly, no ad hoc nested projection
extraction, and no payload reshaping. If the downstream action needs a
different shape, an upstream concept action must emit it explicitly.
Response bodies may use only constants from the target chain row or
fields explicitly emitted by an earlier approved outcome and declared in
`where`. Exact literals are locked: numeric status codes stay numeric,
and string/status values keep their approved casing and hyphenation.

Each sync's `Cites` section names the use-case scenarios it satisfies.
An optional `output/<scenario-name>.sync-summary.md` may be emitted as a
derived, non-canonical per-scenario review table (`Step | Sync | When |
Then | Where summary | Key`) if it is copied mechanically from the
canonical sync files and introduces no new logic.

## Outputs

- `output/LookupUserForLogin.sync.md`
- `output/CheckCredentialForLogin.sync.md`
- `output/RespondUnknownUser.sync.md`
- `output/GrantSessionForLogin.sync.md`
- `output/RespondWrongPassword.sync.md`
- `output/RespondLocked.sync.md`
- `output/RespondLoginSuccess.sync.md`

## Verify

- Every scenario in the use case is satisfied by at least one sync.
- No sync contains `if`/`else` over business state.
- No sync persists state.
- Every sync has a one-row Sync Contract Matrix that names the exact
  source row, target row, `when`, `then`, and allowed literals it was
  derived from.
- Numeric transport status codes remain numeric, not quoted strings.
- String literals and status values preserve their exact approved casing
  and hyphenation.
- Response payloads contain only chain-row constants or fields explicitly
  emitted by earlier approved outcomes and declared in `where:`.
- If any 03 signature differs from 02b or 02, stop and reopen Stage 02
  instead of resolving the mismatch inside a sync.
- **Cross-stage check (back):** every named scenario in
  `../01_usecase/output/usecase.md` is satisfied by at least one sync.
- **Filename contract:** the files in `output/` match the `Outputs`
  section exactly, with no extras and no omissions.

## Gate

Default human approval, with an explicit pass/fail check for the output
filename contract.

## Next stage

→ [`../03a_dependency-review/CONTEXT.md`](../03a_dependency-review/CONTEXT.md) — Dependency review

To advance, the human says: **"Proceed to Stage 03a."**
