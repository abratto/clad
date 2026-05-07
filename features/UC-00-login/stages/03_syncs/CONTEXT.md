# Stage 03 — Synchronizations

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | Scenarios to satisfy |
| `../02_concepts/output/` | 4 | Concepts available to coordinate |
| `../../../../methodology/architecture/SYNCHRONIZATIONS.md` | 3 | Sync semantics |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rules (R3) |
| `../../../../templates/sync.md` | 3 | Output template |

## Process

For each scenario in the use case, identify the chain of concept actions
that fulfils it. Each coordination link becomes one sync. Syncs are
declarative `when … where … then …`; no imperative branching, no state,
no I/O. Each sync's `Cites` section names the use-case scenarios it
satisfies.

## Outputs

- `output/login.sync.md` — couples `PasswordAuth.verify -> Ok` to
  `Session.open` and the HTTP response.

## Verify

- Every scenario in the use case is satisfied by at least one sync, or
  is handled directly by `Web` returning a failure outcome (the
  unhappy paths in UC-00 are the latter).
- No sync contains `if`/`else` over business state.
- No sync persists state.
