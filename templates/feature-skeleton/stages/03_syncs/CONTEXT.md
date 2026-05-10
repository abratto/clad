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
| `../../../../methodology/architecture/SYNC_PATTERNS.md` | 3 | The four legal `where` patterns (A/B/C/D) |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rule R3 |
| `../../../../templates/sync.md` | 3 | Output template |

## Process

Count the transitions in every approved chain table in
`02b_chain-table/output/` for this feature. Each transition (row N →
row N+1) becomes exactly one sync file. Do not collapse multiple
transitions into one sync.

For each transition, write one `<name>.sync.md`:
- `when:` the outcome that fires (e.g. `Account.validate(...) -> Valid`)
- `where:` data-routing only — field-path references and sync constants.
  No function calls, no arithmetic, no I/O. If you need a computation,
  it belongs inside the concept action, not here. Label every line with
  its pattern: `A:` / `B:` / `C:` / `D:` per `SYNC_PATTERNS.md`.
- `then:` the next concept action to invoke.

Syncs are declarative — no imperative branching, no state, no I/O.
Every sync's `Cites` section names the use-case scenario it satisfies.

## Outputs

- `output/<name>.sync.md` — one per coordination rule

## Verify

- No sync contains imperative branching or persists state.
- **Sync count:** the number of sync files in `output/` equals the
  number of transitions in the chain table(s) for this feature (each
  chain-table row-to-row arrow = one sync).
- **Where-clause discipline:** no `where` line contains a function call,
  arithmetic expression, or I/O operation. Every line is a field-path
  reference (`body.field`, `result_of(<#N>).field`) or a sync constant
  (quoted literal). Pattern labels (`A:` / `B:` / `C:` / `D:`) are
  present on every `where` line.
- **Cross-stage check (back):** every named scenario in
  `01_usecase/output/usecase.md` is satisfied by at least one sync, or
  is a `Web`-only failure path (call this out explicitly in the sync
  pack's notes).

## Gate

Default human approval.

## Next stage

→ [`../03a_dependency-review/CONTEXT.md`](../03a_dependency-review/CONTEXT.md) — Dependency review

To advance, the human says: **"Proceed to Stage 03a."**
