<!-- derived from templates/spec.md -->
# UserNaming — SPEC

## Actions

### `register(username) -> RegisterOutcome`

- **Inputs:** `username: String`
- **Outcomes (enum):** `REGISTERED`, `USERNAME_TAKEN`
- **Flow token:** `UserNaming.register { username, userId?, outcome }`

### `lookupByUsername(username) -> Optional<UserId>`

- **Inputs:** `username: String`
- **Outcomes (enum):** `FOUND`, `NOT_FOUND`
- **Flow token:** `UserNaming.lookupByUsername { username, userId?, outcome }`
