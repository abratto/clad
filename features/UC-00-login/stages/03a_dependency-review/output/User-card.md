# Dependency review — `User`

## Section 1 — Invocations received

> No sync invokes any `User` action. `User.lookupByUsername` is
> called inline by `Web` in the `successful-login` and `unknown-user`
> chains; that call is part of `Web`'s routing responsibility, not a
> coordination rule, and so is not a Stage 03 sync.

| Action | Flow (sync) | Data received | Pattern | Source |
|---|---|---|---|---|
| *(none)* | — | — | — | — |

## Section 2 — Named-region reads by others (inbound Pattern D)

None — no other concept's sync reads `User`'s named region.

## Inconsistencies and risks

- `User.lookupByUsername` is reached only via `Web`'s direct
  invocation. If a future flow needs `User.email` (e.g. password
  reset), that read becomes a Pattern D row here and `User` will need
  to expose `email` in its named region.

## Cross-checks

- `lookupByUsername` is declared in `../../02_concepts/output/User.concept.md`.
- No syncs cite `User`.

---

**Do you agree with this card? Any corrections before I continue?**
