# Chain table — `unknown-user`

## Scenario

`unknown-user` — `POST /login` with a username that has no
registered user.

## Chain

| # | When | Then | Inputs | Outcome | Why this step |
|---|---|---|---|---|---|
| 1 | `Web/request[POST /login]` | `Web.request` | `POST /login`, `{ username, password }` | `Routed` | Sole HTTP entry (R4) |
| 2 | `Web.request[Routed]` | `UserNaming.lookupByUsername` | `username` | `Refused` | Username does not exist, precondition fails |
| 3 | `UserNaming.lookupByUsername[Refused]` | `Web.respond[401]` | `401`, `{ message: "username or password didn't match" }` | `Sent` | Same opaque message as `wrong-password` (no enumeration leak) |

## Diagram

```mermaid
stateDiagram-v2
    [*] --> Web_request : POST /login {username, password}
    Web_request --> UserNaming_lookupByUsername : [Routed]
    UserNaming_lookupByUsername --> Web_respond401 : [Refused]
    Web_respond401 --> [*]
```

## Cross-checks

- `Web` and `UserNaming` are listed in the responsibility map and
  `unknown-user` lists both under *Coverage check*.
- No `PasswordAuth.check` row — we never attempt verification when
  the username does not exist (this is what makes the timing-channel
  hardening someone else's problem).

## Notes

- The 401 body is identical to `wrong-password`'s. Stage 03 expresses
  this with two separate syncs that emit the same response template;
  the message constant is shared in code, not the rule.
