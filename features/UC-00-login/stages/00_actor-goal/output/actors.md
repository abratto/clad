<!-- derived from templates/actors.md -->
# Actors — UC-00-login

| Name | Role | Primary concerns |
|---|---|---|
| EndUser | A registered account holder attempting to authenticate to the system | Can sign in quickly with a username and password; is not told whether a username exists on a failed attempt; is told clearly when the account is temporarily locked |

## Out-of-scope actors

- **Administrator** — account management, lockout reset, audit are not part of UC-00-login.
- **Anonymous visitor** — registration is a separate use case.
- **External identity provider** — SSO is out of scope.
