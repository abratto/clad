# UC-00 — Login

## Operational principle

A registered user opens the login page, enters their username and
password, and submits. If the credentials match a registered user and
the account is not locked, a session is opened and the user is
redirected to their landing page; on subsequent requests the session
identifies them. If the credentials do not match, an error message is
shown and they may try again, up to a small number of attempts before
the account is locked.

## Actors

- **User** — a registered account holder attempting to authenticate.

## Scenarios

### Scenario: successful-login

- **Trigger:** `POST /login` with valid `{ username, password }`
- **Pre-conditions:**
  - A registered `User` with that username exists
  - That user has registered a password credential with `PasswordAuth`
  - The account is not in a `Locked` state
- **Expected outcomes:**
  - A new `Session` is opened for the user
  - The response carries a session token
  - Subsequent requests bearing that token are recognised as the user

### Scenario: wrong-password

- **Trigger:** `POST /login` with a username that exists but a
  password that does not match
- **Pre-conditions:**
  - A registered `User` with that username exists
  - The account is not yet at the lockout threshold
- **Expected outcomes:**
  - No session is opened
  - The response shows: *"Username or password didn't match."*
  - The failed-attempt counter for that user increments

### Scenario: unknown-user

- **Trigger:** `POST /login` with a username that has no registered user
- **Expected outcomes:**
  - No session is opened
  - The response shows the same message as wrong-password (no
    enumeration leak)

### Scenario: lockout

- **Trigger:** `POST /login` after the failed-attempt counter has
  reached the lockout threshold
- **Expected outcomes:**
  - No session is opened
  - The response shows: *"Too many attempts. Try again in 15 minutes."*
  - This holds even if the credentials supplied are correct

## Out of scope

- Account registration (separate use case)
- Password reset
- Multi-factor authentication
- Single sign-on
- Email-based identity (UC-00 uses opaque usernames)
- Logout (separate use case; would close the session)
