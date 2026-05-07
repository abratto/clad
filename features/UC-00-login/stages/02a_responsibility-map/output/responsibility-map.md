# Responsibility map — UC-00-login

> One row per concept the feature requires. Choreography lives in
> `../02b_chain-table/output/`; full anatomy lives in
> `../02_concepts/output/<Name>.concept.md`.

## Concepts

| Concept | Owned state (one line) | Owned actions | Notes |
|---|---|---|---|
| `User` | `users: Map<UserId, Username>` | `register`, `lookupByUsername` | Account *creation* is out of UC-00 scope; `register` exists for concept coherence |
| `PasswordAuth` | `credentials: Map<UserId, PasswordHash>`, `failedAttempts: Map<UserId, Int>` | `setCredential`, `check` | Lockout counter belongs here, not in `Session` |
| `Session` | `sessions: Map<SessionId, UserId>` | `grant`, `lookup` | Session lifetime / revocation is out of UC-00 scope |
| `Web` | `(none — bootstrap concept)` | `handle`, `respond` | Sole HTTP entry (R4); see `methodology/architecture/WEB_CONCEPT.md` |

## Coverage check

| Scenario | Concepts touched |
|---|---|
| `successful-login` | `Web`, `User`, `PasswordAuth`, `Session` |
| `wrong-password` | `Web`, `User`, `PasswordAuth` |
| `unknown-user` | `Web`, `User` |
| `lockout` | `Web`, `User`, `PasswordAuth` |

## Out of scope

- `LoginAttemptHistory` — would over-fragment authentication; the
  `failedAttempts` counter on `PasswordAuth` is sufficient.
- `Account` — UC-00-login does not create or close accounts;
  `User.register` is the only lifecycle action and it is out of scope
  for this feature's scenarios.
