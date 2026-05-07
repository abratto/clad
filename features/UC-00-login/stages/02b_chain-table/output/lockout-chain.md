# Chain table — `lockout`

## Scenario

`lockout` — `POST /login` after the failed-attempt counter has
reached the lockout threshold for that user.

## Chain

| # | Concept | Action | Inputs | Outcome | Why this step |
|---|---|---|---|---|---|
| 1 | `Web` | `handle` | `POST /login`, `{ username, password }` | `Routed` | Sole HTTP entry (R4) |
| 2 | `User` | `lookupByUsername` | `username` | `Found(userId)` | The username exists |
| 3 | `PasswordAuth` | `check` | `userId`, `password` | `Locked` | Counter is at threshold; verifier short-circuits regardless of password |
| 4 | `Web` | `respond` | `401`, `{ message: "Too many attempts. Try again in 15 minutes." }` | `Sent` | Distinct message — the lockout state is observable to the user |

## Diagram

```mermaid
sequenceDiagram
    actor U as User
    participant W as Web
    participant Us as User
    participant PA as PasswordAuth
    U->>W: POST /login {username, password}
    W->>Us: lookupByUsername(username)
    Us-->>W: Found(userId)
    W->>PA: check(userId, password)
    PA-->>W: Locked
    W-->>U: 401 {lockout message}
```

## Cross-checks

- `Web`, `User`, `PasswordAuth` are listed in the responsibility map
  and `lockout` lists all three under *Coverage check*.
- The `Locked` outcome is short-circuiting: even a correct password
  yields `Locked`, per `01_usecase/output/usecase.md` §`lockout`.
- The lockout message text differs from `wrong-password` /
  `unknown-user` — the lockout state is intentionally visible.

## Notes

- The counter increment that *causes* the lockout is part of
  `PasswordAuth.check`'s `BadPassword` outcome (see the
  `wrong-password` chain). The `lockout` chain shows what happens on
  the *next* attempt, once the counter is already at threshold.
- This scenario is currently spec-only in the Java profile; the
  `LockoutOnFailedAttempts` sync ships in a follow-up.
