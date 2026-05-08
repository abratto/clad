# Stage 02b — Chain table (UC-00-login)

## Why this stage exists

The **choreography review surface** — one scenario per file, easier to
read than four declarative syncs at once. 02b is also the **canonical
resolver for action-name disputes**: if a sync spec (Stage 03)
disagrees with a chain table, the table wins. That rule is what
reconciled `Session.open` → `Session.grant` and `PasswordAuth.verify` →
`PasswordAuth.check` in this feature — see PR #6.

**Feeds:**

- `<scenario>-chain.md` → 02 (every action used must be declared in the matching concept spec with the same outcome enum), 03 (each row formalises into a sync `when`/`then` link), 03a (the chain is the source of truth for inbound calls per concept), 04c (flow tests assert the chain end-to-end at runtime).

**Agent stance for this stage:** every row is `<Concept>.<action> -> <outcome>`. If you cannot name the outcome, the concept set is wrong — go back to 02a, do not invent.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | UC-00-login scenarios |
| `../02a_responsibility-map/output/responsibility-map.md` | 4 | Available concepts and actions |
| `../../../../methodology/architecture/SYNCHRONIZATIONS.md` | 3 | Forward link to Stage 03 |
| `../../../../templates/chain-table.md` | 3 | Output template |

## Process

For each named scenario in `01_usecase/output/usecase.md`, produce
`output/<scenario-name>-chain.md` using only concepts and actions
from `02a_responsibility-map/output/responsibility-map.md`. The
chain is the ordered list of concept actions that fulfils the
scenario; the last row is `Web.respond`.

## Outputs

- `output/successful-login-chain.md`
- `output/wrong-password-chain.md`
- `output/unknown-user-chain.md`
- `output/lockout-chain.md`

## Verify

- Every scenario has exactly one chain file.
- The first row is `Web.handle`; the last row is `Web.respond`.
- Every action used appears in the responsibility map.

## Gate

Default human approval. **Do you agree with this step? Any
corrections before I continue?**

## Next stage

→ [`../02_concepts/CONTEXT.md`](../02_concepts/CONTEXT.md) — Concept specs (full anatomy)

To advance, the human says: **"Proceed to Stage 02."**
