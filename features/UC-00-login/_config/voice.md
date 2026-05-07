# Voice

Feature-scoped reference (ICM Layer 3) for UC-00-login.

## Error messages

- Use second person ("Your password didn't match.") rather than third
  ("The password supplied is invalid.").
- Do not reveal whether a username exists on a failed login. Both
  unknown-user and wrong-password cases produce the same message:
  *"Username or password didn't match."*
- After lockout: *"Too many attempts. Try again in 15 minutes."*

## Success messages

- No success message on login. The session token's presence and the
  next page are the success signal.

## Field labels

- "Username" (not "Email" or "User ID") — UC-00 doesn't model email.
- "Password" (not "Passphrase" or "Secret").
