# Dependency review — `PasswordAuth`

## Section 1 — Invocations received

| Action | Flow (sync) | Data received | Pattern | Source |
|---|---|---|---|---|
| `check` | `WhenUserLookupByUsernameFoundThenPasswordAuthCheckForLogin` (`successful-login`, `wrong-password`, `lockout`) | `userId`, `password` | A + B | `?p` from `Web/handle` trigger (A); `?user` from `User/lookupByUsername` completion (B) |

> `PasswordAuth/check`'s lockout branch is expressed by the
> `Locked` outcome plus `WhenPasswordAuthCheckLockedThenWebRespondForLogin`, not by a separate `lock`
> action.

## Section 2 — Named-region reads by others (inbound Pattern D)

None — no other concept's sync reads `PasswordAuth`'s named region.

## Inconsistencies and risks

- None at this time. `PasswordAuth` owns the failed-attempt and lockout
  state internally, and Stage 03 branches only on the approved
  `Ok` / `BadPassword` / `Locked` outcomes.

## Cross-checks

- `check` is declared in `../../02_concepts/output/PasswordAuth.concept.md`.
- The sync `WhenUserLookupByUsernameFoundThenPasswordAuthCheckForLogin` exists under `../../03_syncs/output/`.

---

**Do you agree with this card? Any corrections before I continue?**
