# LoginGrantsSession — successful verify opens a session and returns a token

## Rule

```
when:  PasswordAuth.verify(userId, password) -> Ok
then:  Session.open(userId)
       Web.respond(status: 200, body: { sessionId })
```

The `sessionId` in `Web.respond` is the one returned by `Session.open`
on the same trigger; in the implementation profile this binding is
expressed by the runtime's pattern variables.

## Cites

- `../01_usecase/output/usecase.md` — scenario *successful-login*

## Notes

- The unhappy paths (*wrong-password*, *unknown-user*, *lockout*) are
  **not** handled by syncs. They are handled by `Web` translating the
  non-`Ok` outcomes of `PasswordAuth.verify` directly into failure
  responses, with no further fan-out. Keeping non-action outcomes
  syncless is deliberate — there is nothing to coordinate when no
  effect is intended.
- `Web` is also responsible for the *unknown-user* scenario, which it
  reaches by `User.lookupByUsername -> NotFound` (no `verify` is
  attempted). The same opaque error message is returned, satisfying
  the no-enumeration requirement.
