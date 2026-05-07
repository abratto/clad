# User — registered account holder

## State

- `users: Map<UserId, Username>` — the set of registered users and
  their public usernames.

## Actions

### `register(username) -> Created(userId) | UsernameTaken`

- **Inputs:** `username: String`
- **Outputs:**
  - `Created(userId)` — a fresh `UserId` was minted and stored
  - `UsernameTaken` — the username is already in use
- **Effect on state:** on `Created`, adds `userId -> username`.
- **Flow token:** `{ action: "User.register", username, outcome }`

### `lookupByUsername(username) -> Found(userId) | NotFound`

- **Inputs:** `username: String`
- **Outputs:**
  - `Found(userId)` — the username is registered
  - `NotFound` — it is not
- **Effect on state:** none (read-only).
- **Flow token:** `{ action: "User.lookupByUsername", username, outcome }`

## Operational principle

A username is the public name a user is known by; a `UserId` is the
opaque internal identifier other concepts use to refer to that user.
External callers register a username, receive a `UserId`, and from
then on identify the user by that `UserId`. `lookupByUsername` is the
bridge from public name to internal id.

## Notes

- UC-00-login does not invoke `register`; account creation is out of
  scope. The action is listed because the concept owns the lifecycle
  and would not be coherent without it.
