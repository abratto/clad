# LockoutOnFailedAttempts — failed checks accumulate; threshold locks the account

> **Status: spec-only.** The concept action `PasswordAuth.lock(userId)`
> and the failed-attempts counter are not yet in `02_concepts/`. This
> sync is included to demonstrate that one use-case scenario
> (`lockout`) is owned by a sync — not by `Web` — and to anchor the
> matching row in the sync test-intent map.

## Rule

```
when:  PasswordAuth.check(userId, _) -> BAD_PASSWORD
       (counted N times within the lockout window for the same userId)
then:  PasswordAuth.lock(userId)
       Web.respond(status: 401, body: { message: "too many attempts. try again in 15 minutes." })
```

## Cites

- `../01_usecase/output/usecase.md` — scenario *lockout*

## Notes

- The "counted N times within a window" predicate is part of the
  sync-runtime's pattern language, not branching logic in the sync
  body. R3 still holds.
- `wrong-password` and `unknown-user` are deliberately handled by
  `Web` directly (no sync), since they have nothing to coordinate.
