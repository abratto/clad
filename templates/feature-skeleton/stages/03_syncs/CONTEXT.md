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

For each scenario in the use case, identify the chain of concept
actions that fulfils it. Each coordination link becomes one sync.
Syncs are declarative `when … where … then …` — no imperative
branching, no state, no I/O. Every `where` clause must label the
pattern it uses (`A:` / `B:` / `C:` / `D:`) per `SYNC_PATTERNS.md`.
Every sync's `Cites` section names the use-case scenario it
satisfies.

## Outputs

- `output/<name>.sync.md` — one per coordination rule

## Verify

- No sync contains imperative branching or persists state.
- **Cross-stage check (back):** every named scenario in
  `01_usecase/output/usecase.md` is satisfied by at least one sync, or
  is a `Web`-only failure path (call this out explicitly in the sync
  pack's notes).

## Gate

Default human approval.
