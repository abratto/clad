# PasswordAuth — verify a principal by username + password

## State

```
credentials(userId: UserId) -> passwordHash: PasswordHash   -- mandatory
failedAttempts(userId: UserId) -> count: Int                -- mandatory, default 0
lockedUntil(userId: UserId) -> timestamp: Timestamp         -- optional
```

(`PasswordHash` is an opaque type for a salted, slow-hashed password.
The hashing scheme is an implementation detail, not part of the spec.)

## Actions

```
setPassword [ userId: UserId ; password: String ] => [ ok ]
    stores hash(password) in credentials[userId]
    clears any failedAttempts[userId] and lockedUntil[userId]
    flow token: { action: "PasswordAuth.setPassword", userId, outcome: "ok" }

verify [ userId: UserId ; password: String ] => [ ok ]
    password matched credentials[userId] and account is not locked
    clears failedAttempts[userId]
    flow token: { action: "PasswordAuth.verify", userId, outcome: "ok" }
    note: password is never in the flow token

verify [ userId: UserId ; password: String ] => [ error: "invalidPassword" ]
    userId is registered but password did not match
    increments failedAttempts[userId]; if counter reaches threshold (5),
    sets lockedUntil[userId] to now + 15 minutes

verify [ userId: UserId ; password: String ] => [ error: "locked" ]
    lockedUntil[userId] is in the future
    no state change

verify [ userId: UserId ; password: String ] => [ error: "unknownPrincipal" ]
    userId has no registered credential
    no state change
```

## Operational principle

```
after  PasswordAuth/setPassword: [ userId: u ; password: p ] => [ ok ]
then   PasswordAuth/verify:      [ userId: u ; password: p ] => [ ok ]
-- repeated wrong passwords accumulate --
then   PasswordAuth/verify:      [ userId: u ; password: wrong ] => [ error: "invalidPassword" ]
-- (× 5 — account locks) --
then   PasswordAuth/verify:      [ userId: u ; password: p ] => [ error: "locked" ]
```

## Notes

- `PasswordAuth` does not know anything about usernames, sessions, or
  HTTP. Its only currency is `UserId`.
- The lockout threshold (5) and duration (15 min) are implementation
  parameters, not part of the contract surface.
