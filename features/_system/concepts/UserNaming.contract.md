<!-- canonical — derived from concept UserNaming: introduced-by UC-00-login, current source UC-00-login -->
# UserNaming — contract

## Actions

### `register(username) -> RegisterOutcome`

- **Inputs:** `username: String`
- **Outcomes (enum):** `REGISTERED`, `REFUSED`
- **Flow token:** `UserNaming.register { username, userId?, outcome }`

### `lookupByUsername(username) -> Optional<UserId>`

- **Inputs:** `username: String`
- **Outcomes (enum):** `FOUND`, `REFUSED`
- **Flow token:** `UserNaming.lookupByUsername { username, userId?, outcome }`
