# Dependency review — `User`

## Section 1 — Invocations received

| Action | Flow (sync) | Data received | Pattern | Source |
|---|---|---|---|---|
| `lookupByUsername` | `WhenWebHandleRoutedThenUserLookupByUsernameForLogin` (`successful-login`, `wrong-password`, `unknown-user`, `lockout`) | `username` | A | `Web/handle` trigger `?u` |

## Section 2 — Named-region reads by others (inbound Pattern D)

None — no other concept's sync reads `User`'s named region.

## Inconsistencies and risks

- `User/lookupByUsername` is reached only via `Web`'s direct
  invocation. If a future flow needs `User.email` (e.g. password
  reset), that read becomes a Pattern D row here and `User` will need
  to expose `email` in its named region.

## Cross-checks

- `lookupByUsername` is declared in `../../02_concepts/output/User.concept.md`.
- The sync `WhenWebHandleRoutedThenUserLookupByUsernameForLogin` exists under `../../03_syncs/output/`.

---

**Do you agree with this card? Any corrections before I continue?**
