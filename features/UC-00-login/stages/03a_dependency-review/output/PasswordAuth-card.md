# Dependency review — `PasswordAuth`

## Section 1 — Invocations received

| Action | Flow (sync) | Data received | Pattern | Source |
|---|---|---|---|---|
| `lock` | `LockoutOnFailedAttempts` (`lockout`) | `userId` | — | Trigger pattern variable from `when: PasswordAuth.check(userId, _) -> BAD_PASSWORD` |

> The `check` action itself is invoked inline by `Web` (per the
> chain tables) — not by a sync. It appears here only as the
> *trigger* of `LockoutOnFailedAttempts`, not as a `then` target.

## Section 2 — Named-region reads by others (inbound Pattern D)

None — no other concept's sync reads `PasswordAuth`'s named region.

## Inconsistencies and risks

- The `LockoutOnFailedAttempts` sync is **spec-only** in this
  iteration; the `lock` action does not yet exist in
  `02_concepts/output/PasswordAuth.concept.md`. Stage 04 will fail
  fast on this if not closed first.
- The lockout window predicate ("counted N times within window")
  must be supplied by the sync runtime, not by branching inside the
  sync — see `LockoutOnFailedAttempts.sync.md` notes.

## Cross-checks

- `lock` is referenced by `../../03_syncs/output/LockoutOnFailedAttempts.sync.md` and
  must be added to `../../02_concepts/output/PasswordAuth.concept.md`
  before Stage 04.
- `check` is declared in `../../02_concepts/output/PasswordAuth.concept.md`.

---

**Do you agree with this card? Any corrections before I continue?**
