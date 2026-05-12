# Session — bearer-token sessions for a principal

## State

```
session(sessionId: SessionId) -> userId: UserId      -- mandatory
session(sessionId: SessionId) -> openedAt: Timestamp -- mandatory
```

## Actions

```
open [ userId: UserId ] => [ sessionId: SessionId ]
    mints a fresh, unguessable SessionId and records userId + now()
    flow token: { action: "Session.open", userId, sessionId, outcome: "opened" }

resolve [ sessionId: SessionId ] => [ userId: UserId ]
    session exists — returns the principal it represents
    no state change
    flow token: { action: "Session.resolve", sessionId, outcome: "principal" }

resolve [ sessionId: SessionId ] => [ error: "unknown" ]
    no such session exists
    no state change

close [ sessionId: SessionId ] => [ ok ]
    session existed and has been removed
    flow token: { action: "Session.close", sessionId, outcome: "closed" }

close [ sessionId: SessionId ] => [ error: "unknown" ]
    no such session exists
    no state change
```

## Operational principle

```
after  Session/open:    [ userId: u ]          => [ sessionId: s ]
then   Session/resolve: [ sessionId: s ]       => [ userId: u ]
then   Session/close:   [ sessionId: s ]       => [ ok ]
then   Session/resolve: [ sessionId: s ]       => [ error: "unknown" ]
```

## Notes

- `SessionId` must be unguessable (e.g. 128 bits of randomness,
  base64url). The exact scheme is an implementation detail.
- `Session` does not authenticate anyone — that is `PasswordAuth`'s
  job — it only records that an authentication has happened and exposes
  its consequence.
- UC-00-login does not invoke `close`; logout is out of scope.
