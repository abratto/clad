# PasswordAuth — verify a principal by username + password

## State

- `credentials: Map<UserId, PasswordHash>` — registered password hashes.
- `failedAttempts: Map<UserId, Int>` — consecutive failure counter.
- `lockedUntil: Map<UserId, Timestamp>` — when present, the account is
  locked until that time.

(`PasswordHash` is an opaque type for a salted, slow-hashed password.
The hashing scheme is an implementation detail, not part of the spec.)

## Actions

### `setPassword(userId, password) -> Ok`

- **Inputs:** `userId: UserId`, `password: String`
- **Outputs:** `Ok`
- **Effect on state:** stores `hash(password)` in `credentials[userId]`;
  clears any `failedAttempts[userId]` and `lockedUntil[userId]`.
- **Flow token:** `{ action: "PasswordAuth.setPassword", userId, outcome: "Ok" }`

### `verify(userId, password) -> Ok | InvalidPassword | UnknownPrincipal | Locked`

- **Inputs:** `userId: UserId`, `password: String`
- **Outputs:**
  - `Ok` — the password matched and the account is not locked
  - `InvalidPassword` — `userId` is registered but the password did not
    match
  - `UnknownPrincipal` — `userId` has no registered credential
  - `Locked` — `lockedUntil[userId]` is in the future
- **Effect on state:**
  - On `Ok`: clears `failedAttempts[userId]`.
  - On `InvalidPassword`: increments `failedAttempts[userId]`. If the
    counter reaches the lockout threshold (5), sets
    `lockedUntil[userId]` to *now + 15 minutes*.
  - On `Locked` and `UnknownPrincipal`: no state change.
- **Flow token:** `{ action: "PasswordAuth.verify", userId, outcome }`
  (the password is *never* in the token).

## Operational principle

A credential is established by `setPassword`. Thereafter, a caller
proves identity by calling `verify` with the supplied password. After
five consecutive `InvalidPassword` outcomes the account is `Locked` for
15 minutes; further `verify` calls return `Locked` regardless of the
password supplied. A successful `verify` resets the failure counter.

## Notes

- `PasswordAuth` does not know anything about usernames, sessions, or
  HTTP. Its only currency is `UserId`.
- The lockout threshold and duration are implementation parameters,
  not part of the contract surface.
