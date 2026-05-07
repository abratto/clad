# Stage 03 — Synchronizations

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
