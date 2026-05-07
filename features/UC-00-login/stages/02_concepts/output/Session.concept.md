# Session — bearer-token sessions for a principal

## State

- `sessions: Map<SessionId, { userId: UserId, openedAt: Timestamp }>`
  — open sessions and the principals they represent.

## Actions

### `open(userId) -> Opened(sessionId)`

- **Inputs:** `userId: UserId`
- **Outputs:** `Opened(sessionId)` — a fresh, unguessable
  `SessionId` was minted and recorded.
- **Effect on state:** adds `sessionId -> { userId, now() }`.
- **Flow token:** `{ action: "Session.open", userId, sessionId, outcome: "Opened" }`

### `resolve(sessionId) -> Principal(userId) | Unknown`

- **Inputs:** `sessionId: SessionId`
- **Outputs:**
  - `Principal(userId)` — the session is open for that user
  - `Unknown` — no such session
- **Effect on state:** none.
- **Flow token:** `{ action: "Session.resolve", sessionId, outcome }`

### `close(sessionId) -> Closed | Unknown`

- **Inputs:** `sessionId: SessionId`
- **Outputs:** `Closed` if the session existed and was removed,
  `Unknown` otherwise.
- **Effect on state:** removes `sessionId` from `sessions`.
- **Flow token:** `{ action: "Session.close", sessionId, outcome }`

## Operational principle

After authentication elsewhere, a session is opened by `open(userId)`
and a `SessionId` is returned to the caller. The caller presents that
`SessionId` on later requests; `resolve` exchanges it for the
authenticated `UserId`. `close` ends the session. `Session` does not
authenticate anyone — that is `PasswordAuth`'s job — it only records
that an authentication has happened and exposes its consequence.

## Notes

- `SessionId` must be unguessable (e.g. 128 bits of randomness,
  base64url). The exact scheme is an implementation detail.
- UC-00-login does not invoke `close`; logout is out of scope.
