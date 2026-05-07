# Dependency review — `Session`

## Section 1 — Invocations received

| Action | Flow (sync) | Data received | Pattern | Source |
|---|---|---|---|---|
| `grant` (sync says `open`) | `LoginGrantsSession` (`successful-login`) | `userId` | — | Trigger pattern variable from `when: PasswordAuth.verify(userId, password) -> Ok` |

## Section 2 — Named-region reads by others (inbound Pattern D)

None — no other concept's sync reads `Session`'s named region. The
`sessionId` returned by `grant` is consumed by the same sync's
`Web.respond` invocation (Pattern B — flow-sibling output of
`Session.grant`) and so is not a Pattern D read against `Session`'s
state.

## Inconsistencies and risks

- **Action-name discrepancy.** The chain table calls the action
  `Session.grant` returning `Granted(sessionId)`; the sync spec
  writes `Session.open(userId, session)`. These name the same
  action; the chain table is canonical (per
  [`../../../templates/chain-table.md`](../../../templates/chain-table.md)).
  Stage 03 sync spec should be reconciled to `grant` before Stage 04.
- Similarly the sync's `when` clause writes
  `PasswordAuth.verify` while the chain writes `PasswordAuth.check`
  with outcome `Ok`. Same defect, same resolution.

## Cross-checks

- `grant` is declared in `../../02_concepts/output/Session.concept.md`.
- The sync `LoginGrantsSession` exists under `../../03_syncs/output/`.

---

**Do you agree with this card? Any corrections before I continue?**
