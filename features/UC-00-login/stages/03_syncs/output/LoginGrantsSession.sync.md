# LoginGrantsSession — successful check opens a session and returns a token

## Rule

```
when:  PasswordAuth.check(userId, password) -> Ok
where: B: sessionId = result_of(Session.grant).sessionId
then:  Session.grant(userId)
       Web.respond(status: 200, body: { sessionToken: sessionId })
```

The `sessionId` in `Web.respond` is the one returned by `Session.grant`
on the same trigger; in the implementation profile this binding is
expressed by the runtime's pattern variables, with the join labelled
as Pattern B (flow-sibling) per
[`SYNC_PATTERNS.md`](../../../../../methodology/architecture/SYNC_PATTERNS.md).

## Cites

- `../01_usecase/output/usecase.md` — scenario *successful-login*

## Notes

- Action names match the canonical chain tables under
  `../02b_chain-table/output/`: `PasswordAuth.check` (not `verify`)
  and `Session.grant` (not `open`).
- The unhappy paths (*wrong-password*, *unknown-user*, *lockout*) are
  **not** handled by this sync. *wrong-password* and *unknown-user*
  are handled by `Web` translating the non-`Ok` outcomes of
  `PasswordAuth.check` and `User.lookupByUsername` directly into 401
  responses with no further fan-out (no Stage 03 coordination is
  needed when no effect is intended). *lockout* is owned by
  `LockoutOnFailedAttempts.sync.md`.
- `Web` reaches the *unknown-user* path via
  `User.lookupByUsername -> NotFound` (no `check` is attempted). The
  same opaque error message is returned, satisfying the
  no-enumeration requirement.
