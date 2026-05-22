# Dependency review — `PasswordAuth`

## Section 1 — Invocations received

| Action | Flow (sync) | Data received | Pattern | Source |
|---|---|---|---|---|
| `check` | `CheckCredentialForLogin` (`successful-login`, `wrong-password`, `lockout`) | `userId`, `password` | A | `password` from `body.password`; `userId` carried directly by `when: User.lookupByUsername[Found(userId)]` |

> `PasswordAuth.check` is now a normal sync target under
> `CheckCredentialForLogin`; the lockout branch is expressed by the
> `Locked` outcome plus `RespondLocked`, not by a separate `lock`
> action.

## Section 2 — Named-region reads by others (inbound Pattern D)

None — no other concept's sync reads `PasswordAuth`'s named region.

## Inconsistencies and risks

- None at this time. `PasswordAuth` owns the failed-attempt and lockout
  state internally, and Stage 03 now branches only on the approved
  `Ok` / `BadPassword` / `Locked` outcomes.

## Cross-checks

- `check` is declared in `../../02_concepts/output/PasswordAuth.concept.md`.
- The sync `CheckCredentialForLogin` exists under `../../03_syncs/output/`.

---

**Do you agree with this card? Any corrections before I continue?**
