<!-- canonical — derived from concept Session: introduced-by UC-00-login, current source UC-00-login -->
# Session — contract

## Actions

### `grant(userId) -> SessionId`

- **Inputs:** `userId: UserId`
- **Outcomes (enum):** `GRANTED`
- **Flow token:** `Session.grant { userId, sessionId, outcome }`

### `lookup(sessionId) -> Optional<UserId>`

- **Inputs:** `sessionId: SessionId`
- **Outcomes (enum):** `FOUND`, `UNKNOWN`
- **Flow token:** `Session.lookup { sessionId, userId?, outcome }`
