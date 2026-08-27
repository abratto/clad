# Dependency review — `UserNaming`

## Section 1 — Invocations received

| Action | Flow (sync) | Data received | Pattern | Source |
|---|---|---|---|---|
| `lookupByUsername` | `WhenWebHandleRoutedThenUserNamingLookupByUsernameForLogin` (`successful-login`, `wrong-password`, `unknown-user`, `lockout`) | `username` | A | `Web/handle` trigger `?u` |

## Section 2 — Named-region reads by others (inbound Pattern D)

None — no other concept's sync reads `UserNaming`'s named region.

## Inconsistencies and risks

- `UserNaming/lookupByUsername` is reached only via `Web`'s direct
  invocation. If a future flow needs `UserNaming.email` (e.g. password
  reset), that read becomes a Pattern D row here and `UserNaming` will need
  to expose `email` in its named region.

## Cross-checks

- `lookupByUsername` is declared in `../../02_concepts/output/UserNaming.concept.md`.
- The sync `WhenWebHandleRoutedThenUserNamingLookupByUsernameForLogin` exists under `../../03_syncs/output/`.

---

**Do you agree with this card? Any corrections before I continue?**
