<!-- proposal snapshot — derived from templates/contract.md; canonical contract: features/_system/concepts/UserNaming.contract.md -->
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
