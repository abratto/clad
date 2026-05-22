<!-- derived from templates/spec.md -->
# User — SPEC

## Actions

### `register(username) -> RegisterOutcome`

- **Inputs:** `username: String`
- **Outcomes (enum):** `REGISTERED`, `USERNAME_TAKEN`
- **Flow token:** `User.register { username, userId?, outcome }`

### `lookupByUsername(username) -> Optional<UserId>`

- **Inputs:** `username: String`
- **Outcomes (enum):** `FOUND`, `NOT_FOUND`
- **Flow token:** `User.lookupByUsername { username, userId?, outcome }`
