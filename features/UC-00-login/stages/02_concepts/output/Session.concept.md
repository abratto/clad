# Session — bearer-token sessions for a principal

## State

```
session(sessionId: SessionId) -> userId: UserId      -- mandatory
session(sessionId: SessionId) -> openedAt: Timestamp -- mandatory
```

## Actions

```
grant [ userId: UserId ] => [ sessionId: SessionId ]
    mints a fresh, unguessable SessionId and records userId + now()
    flow token: { action: "Session.grant", userId, sessionId, outcome: "granted" }

lookup [ sessionId: SessionId ] => [ userId: UserId ]
    session exists — returns the principal it represents
    no state change
    flow token: { action: "Session.lookup", sessionId, outcome: "found" }

lookup [ sessionId: SessionId ] => [ error: "unknown" ]
    no such session exists
    no state change
```

## Operational principle

```
after  Session/grant:   [ userId: u ]          => [ sessionId: s ]
then   Session/lookup:  [ sessionId: s ]       => [ userId: u ]
then   Session/lookup:  [ sessionId: missing ] => [ error: "unknown" ]
```

## Notes

- `SessionId` must be unguessable (e.g. 128 bits of randomness,
  base64url). The exact scheme is an implementation detail.
- `Session` does not authenticate anyone — that is `PasswordAuth`'s
  job — it only records that an authentication has happened and exposes
  its consequence.
- Logout is out of scope for UC-00-login, so `close` is omitted from
    this feature slice.
- Stage 02b renders the happy-path `grant` outcome as
    `Granted(sessionId)`; that token is the chain-table/sync view of the
    action case above.
