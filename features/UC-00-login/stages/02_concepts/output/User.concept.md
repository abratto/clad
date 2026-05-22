# User — registered account holder

## State

```
user(userId: UserId) -> username: String   -- mandatory, unique across all users
```

## Actions

```
register [ username: String ] => [ userId: UserId ]
    username is not already in use
    mints a fresh UserId and records username -> userId
    flow token: { action: "User.register", username, userId, outcome: "created" }

register [ username: String ] => [ error: "usernameTaken" ]
    username is already in use
    no state change

lookupByUsername [ username: String ] => [ userId: UserId ]
    username is registered — returns the corresponding UserId
    no state change
    flow token: { action: "User.lookupByUsername", username, userId, outcome: "found" }

lookupByUsername [ username: String ] => [ error: "notFound" ]
    username is not registered
    no state change
```

## Operational principle

```
after  User/register:         [ username: "alice" ] => [ userId: u ]
then   User/lookupByUsername:  [ username: "alice" ] => [ userId: u ]
```

## Notes

- A `UserId` is the opaque internal identifier other concepts use to
  refer to a user. External callers register a username, receive a
  `UserId`, and from then on identify the user by that `UserId`.
- UC-00-login does not invoke `register`; account creation is out of
  scope. The action is listed because the concept owns the lifecycle
  and would not be coherent without it.
- Stage 02b renders the happy-path lookup outcome as
    `Found(userId)` and the miss path as `NotFound`; those tokens are the
    chain-table/sync view of the same two action cases above.
