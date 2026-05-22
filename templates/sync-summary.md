# Sync summary — `<scenario-name>`

> **Status: Derived, non-canonical view.** This file summarizes the
> Stage 03 sync pack for one scenario in a compact review table. The
> canonical artefacts remain the per-sync `output/*.sync.md` files.

## Scenario

- `<scenario-name>`

## Sync summary table

| Step | Sync | When | Then | Where summary | Key |
|---|---|---|---|---|---|
| 1 | `<SyncName>` | `<when token>` | `<then token>` | `A: body.foo; C: role=ADMIN` | `flow token` |
| 2 | `<SyncName>` | `<when token>` | `<then token>` | `B: result_of(#1).id` | `flow token` |
| 90 | `<SyncName>` | `<when token>` | `Web.respond[4xx]` | `—` | `—` |

## Derivation rule

- Every row must be copied from an approved canonical sync file.
- `When` and `Then` must match the sync file verbatim.
- `Where summary` may abbreviate the canonical `where:` lines, but it
  may not add bindings, logic, or computed fields.
- `Key` may summarize the binding source (`flow token`, `result_of(#2)`,
  named graph key), but it may not invent new routing semantics.