<!-- derived from templates/spec.md -->
# PasswordAuth — SPEC

## Actions

### `setCredential(userId, passwordVerifier) -> void`

- **Inputs:** `userId: UserId`, `passwordVerifier: String`
- **Outcomes:** `STORED` (always)
- **Flow token:** `PasswordAuth.setCredential { userId, outcome }`

### `check(userId, password) -> AuthOutcome`

- **Inputs:** `userId: UserId`, `password: String`
- **Outcomes (enum):** `OK`, `BAD_PASSWORD`, `LOCKED`
- **Flow token:** `PasswordAuth.check { userId, outcome }`

## Notes

- UC-00-login now treats lockout as an internal `PasswordAuth.check`
  outcome, not as a separate sync-owned action.
