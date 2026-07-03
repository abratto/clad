# Dependency review — `Session`

## Section 1 — Invocations received

| Action | Flow (sync) | Data received | Pattern | Source |
|---|---|---|---|---|
| `grant` | `WhenPasswordAuthCheckOkThenSessionGrantForLogin` (`successful-login`) | `userId` | B | `PasswordAuth/check` completion `?user` |

## Section 2 — Named-region reads by others (inbound Pattern D)

None — no other concept's sync reads `Session`'s named region. The
`sessionId` returned by `grant` is consumed by `WhenSessionGrantGrantedThenWebRespondForLogin`
(Pattern B — flow-sibling output of `Session/grant`) and so is not a
Pattern D read against `Session`'s state.

## Inconsistencies and risks

- None at this time. (A previous draft of the sync pack used `Session/open`
  and `PasswordAuth/verify`; reconciled to the canonical chain-table names
  `Session/grant` and `PasswordAuth/check`.)

## Cross-checks

- `grant` is declared in `../../02_concepts/output/Session.concept.md`.
- The sync `WhenPasswordAuthCheckOkThenSessionGrantForLogin` exists under `../../03_syncs/output/`.

---

**Do you agree with this card? Any corrections before I continue?**
