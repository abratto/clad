<!-- derived from templates/goals.md -->
# Goals — UC-00-login

## In scope

| Actor | Goal | Priority | In scope |
|---|---|---|---|
| EndUser | wants to **sign in with username and password** so that **subsequent requests are recognised as them** | must | yes |
| EndUser | wants to **see a clear, non-enumerating error** on a failed attempt so that **they know to retry without learning whether the username exists** | must | yes |
| EndUser | wants to **be told when the account is temporarily locked** so that **they understand why retrying does not work** | should | yes |

## Out of scope

- Account registration (separate use case)
- Password reset / change
- Multi-factor authentication
- Single sign-on / federated identity
- Email-based identity (UC-00 uses opaque usernames)
- Logout (separate use case)
