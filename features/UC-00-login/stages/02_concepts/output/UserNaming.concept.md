concept UserNaming [UserId]
purpose
    to associate usernames with opaque user identifiers

## State

```
username: UserId -> String   -- mandatory, unique across all users
```

## Actions

```
register [ username: String ] => [ userId: UserId ]
    precondition {
        username not in Cod(State.username)
    }
    postcondition {
        State.username'[userId] = username
        userId is freshly minted
    }
    flow token: { action: "UserNaming.register", username, userId, outcome: "REGISTERED" }

lookupByUsername [ username: String ] => [ userId: UserId ]
    precondition {
        username in Dom(State.username)
    }
    postcondition {
        State.username[userId] == username
    }
    no state change
    flow token: { action: "UserNaming.lookupByUsername", username, userId, outcome: "FOUND" }
```

## Operational principle

```
after  UserNaming/register:         [ username: "alice" ] => [ userId: u ]
then  UserNaming/lookupByUsername:  [ username: "alice" ] => [ userId: u ]
```

## Notes

- A `UserId` is the opaque internal identifier other concepts use to
  refer to a user. External callers register a username, receive a
  `UserId`, and from then on identify the user by that `UserId`.
- UC-00-login does not invoke `register`; account creation is out of
  scope. The action is listed because the concept owns the lifecycle
  and would not be coherent without it.
- Precondition failures cause **refusal** (`:outcome "refused"`) — the
  action does not execute, no state changes, and refusal is surfaced as
  an RDF-star completion that syncs match on. Error outcomes within the
  concept formal vocabulary (`error: "..."`) are reserved for
  state-mutating failures (e.g., `PasswordAuth.check` increments
  `failedAttempts` even on a wrong password).
