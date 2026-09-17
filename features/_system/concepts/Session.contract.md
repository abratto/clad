<!-- derived from templates/spec.md -->
# Session — SPEC

## Actions

### `grant(userId) -> SessionId`

- **Inputs:** `userId: UserId`
- **Outcomes (enum):** `GRANTED`
- **Flow token:** `Session.grant { userId, sessionId, outcome }`

### `lookup(sessionId) -> Optional<UserId>`

- **Inputs:** `sessionId: SessionId`
- **Outcomes (enum):** `FOUND`, `UNKNOWN`
- **Flow token:** `Session.lookup { sessionId, userId?, outcome }`
