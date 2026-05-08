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
that fulfils it. Each coordination link becomes one sync. Syncs are
declarative `when … where … then …`; no imperative branching, no state,
no I/O. Each sync's `Cites` section names the use-case scenarios it
satisfies.

## Outputs

- `output/LoginGrantsSession.sync.md` — couples `PasswordAuth.check -> OK` to `Session.grant` and the 200 response.
- `output/LockoutOnFailedAttempts.sync.md` — spec-only this iteration; pairs N consecutive `BAD_PASSWORD` outcomes with `PasswordAuth.lock` and a 401 response.

## Verify

- Every scenario in the use case is satisfied by at least one sync, or
  is handled directly by `Web` returning a failure outcome (the
  `wrong-password` and `unknown-user` paths in UC-00 are the latter —
  documented in `LoginGrantsSession.sync.md` notes).
- No sync contains `if`/`else` over business state.
- No sync persists state.
- **Cross-stage check (back):** every named scenario in
  `../01_usecase/output/usecase.md` is satisfied by at least one sync
  or is explicitly called out as a `Web`-only failure path.

## Gate

Default human approval.

## Next stage

→ [`../03a_dependency-review/CONTEXT.md`](../03a_dependency-review/CONTEXT.md) — Dependency review

To advance, the human says: **"Proceed to Stage 03a."**
