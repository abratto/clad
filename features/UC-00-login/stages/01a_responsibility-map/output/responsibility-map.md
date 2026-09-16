# Responsibility map — UC-00-login

> One row per concept the feature requires. Choreography lives in
> `../01b_chain-table/output/`; full anatomy lives in the canonical corpus
> `features/_system/concepts/<Name>.concept.md` (UC-00 introduced these
> concepts; the feature's proposals shadow the corpus by name).

## Concepts

| Concept | Origin | Owned state (one line) | Owned actions | Notes |
|---|---|---|---|---|
| `UserNaming` | `new` | `users: Map<UserId, Username>` | `register`, `lookupByUsername` | Account *creation* is out of UC-00 scope; `register` exists for concept coherence |
| `PasswordAuth` | `new` | `credentials: Map<UserId, PasswordHash>`, `failedAttempts: Map<UserId, Int>` | `setCredential`, `check` | Lockout counter belongs here, not in `Session` |
| `Session` | `new` | `sessions: Map<SessionId, UserId>` | `grant`, `lookup` | Session lifetime / revocation is out of UC-00 scope |
| `Web` | `new` | `(none — bootstrap concept)` | `handle`, `respond` | Sole HTTP entry (R4); see `methodology/architecture/WEB_CONCEPT.md` |

## Proposals

> UC-00-login is the worked example that introduced the vocabulary, so every
> row is `new`. Each proposal is authored in this feature's Stage-02 output and
> was promoted into the corpus (`introduced-by UC-00-login`).

| Concept | Kind | Proposed addition (actions / state) | Requires (dependence claim) | Rationale |
|---|---|---|---|---|
| `UserNaming` | `new` | `register`, `lookupByUsername`; `username: UserId -> String` | — | Naming is independent of authenticating (G1) |
| `PasswordAuth` | `new` | `setCredential`, `check`; `passwordHash`, `failedAttempts`, `lockedUntil` | `UserNaming` | Needs a `UserId`; `UserNaming` is the app's only supplier |
| `Session` | `new` | `grant`, `lookup`; `userId`, `openedAt` | `UserNaming` | Records a principal as a `UserId`, supplied by `UserNaming` |

## Coverage check

| Scenario | Concepts touched |
|---|---|
| `successful-login` | `Web`, `UserNaming`, `PasswordAuth`, `Session` |
| `wrong-password` | `Web`, `UserNaming`, `PasswordAuth` |
| `unknown-user` | `Web`, `UserNaming` |
| `lockout` | `Web`, `UserNaming`, `PasswordAuth` |

## Out of scope

- `LoginAttemptHistory` — would over-fragment authentication; the
  `failedAttempts` counter on `PasswordAuth` is sufficient.
- `Account` — UC-00-login does not create or close accounts;
  `UserNaming.register` is the only lifecycle action and it is out of scope
  for this feature's scenarios.
