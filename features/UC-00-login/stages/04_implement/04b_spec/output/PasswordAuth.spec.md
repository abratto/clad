<!-- derived from templates/spec.md -->
# PasswordAuth — SPEC

## Actions

### `setCredential(userId, passwordVerifier) -> void`

- **Inputs:** `userId: UserId`, `passwordVerifier: String`
- **Outcomes:** `STORED` (always)
- **Flow token:** `PasswordAuth.setCredential { userId, outcome }`

### `check(userId, password) -> AuthOutcome`

- **Inputs:** `userId: UserId`, `password: String`
- **Outcomes (enum):** `OK`, `BAD_PASSWORD`, `NO_CREDENTIAL`
- **Flow token:** `PasswordAuth.check { userId, outcome }`

## Notes

- UC-00-login does not exercise lockout in this slice; the
  `LockoutOnFailedAttempts` sync adds counter state in a follow-up
  iteration. SPEC will gain a `getFailedAttempts(userId)` action then.
