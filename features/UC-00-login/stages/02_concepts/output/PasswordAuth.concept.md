concept PasswordAuth [UserId]
purpose
    to verify a principal by userId + password

## State

```
passwordHash: UserId -> PasswordHash     -- mandatory
failedAttempts: UserId -> Int            -- mandatory, default 0
lockedUntil: UserId -> Timestamp         -- optional
```

## Actions

```
setCredential [ userId: UserId ; password: String ] => [ ok ]
    stores hash(password) in credentials[userId]
    clears any failedAttempts[userId] and lockedUntil[userId]
    flow token: { action: "PasswordAuth.setCredential", userId, outcome: "ok" }

check [ userId: UserId ; password: String ] => [ ok ]
    password matched credentials[userId] and account is not locked
    clears failedAttempts[userId]
    flow token: { action: "PasswordAuth.check", userId, outcome: "ok" }
    note: password is never in the flow token

check [ userId: UserId ; password: String ] => [ error: "badPassword" ]
    userId is registered but password did not match
    increments failedAttempts[userId]; if counter reaches threshold (5),
    sets lockedUntil[userId] to now + 15 minutes

check [ userId: UserId ; password: String ] => [ error: "locked" ]
    lockedUntil[userId] is in the future
    no state change
```

## Operational principle

```
after  PasswordAuth/setCredential: [ userId: u ; password: p ] => [ ok ]
then  PasswordAuth/check:         [ userId: u ; password: p ] => [ ok ]
-- repeated wrong passwords accumulate --
then  PasswordAuth/check:         [ userId: u ; password: wrong ] => [ error: "badPassword" ]
-- (x 5 — account locks) --
then  PasswordAuth/check:         [ userId: u ; password: p ] => [ error: "locked" ]
```

## Notes

- `PasswordAuth` does not know anything about usernames, sessions, or
  HTTP. Its only currency is `UserId`.
- The lockout threshold (5) and duration (15 min) are implementation
  parameters, not part of the contract surface.
- `unknown-user` is resolved upstream by `User.lookupByUsername`; UC-00
  therefore does not need an `unknownPrincipal` outcome here.
