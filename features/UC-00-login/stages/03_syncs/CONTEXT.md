# Stage 03 — Synchronizations

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
