concept User [UserId]
purpose
    to associate usernames with opaque user identifiers

## State

```
username: UserId -> String   -- mandatory, unique across all users
```

## Actions

```
register [ username: String ] => [ userId: UserId ]
    username is not already in use
    mints a fresh UserId and records the username mapping
    flow token: { action: "User.register", username, userId, outcome: "REGISTERED" }

register [ username: String ] => [ error: "usernameTaken" ]
    username is already in use — no state change

lookupByUsername [ username: String ] => [ userId: UserId ]
    username is registered — returns the corresponding UserId
    no state change
    flow token: { action: "User.lookupByUsername", username, userId, outcome: "FOUND" }

lookupByUsername [ username: String ] => [ error: "notFound" ]
    username is not registered — no state change
```

## Operational principle

```
after  User/register:         [ username: "alice" ] => [ userId: u ]
then  User/lookupByUsername:  [ username: "alice" ] => [ userId: u ]
```

## Notes

- A `UserId` is the opaque internal identifier other concepts use to
  refer to a user. External callers register a username, receive a
  `UserId`, and from then on identify the user by that `UserId`.
- UC-00-login does not invoke `register`; account creation is out of
  scope. The action is listed because the concept owns the lifecycle
  and would not be coherent without it.
