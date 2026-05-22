# RespondUnknownUser — unknown usernames return the opaque 401 response

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `2` | `3a` | `User.lookupByUsername[NotFound]` | `Web.respond(status=401, body={ message: "username or password didn't match" })` | `401`, `"username or password didn't match"` |

## Rule

```
when:  User.lookupByUsername[NotFound]
then:  Web.respond(status=401, body={ message: "username or password didn't match" })
```

## Cites

- `../01_usecase/output/usecase.md` — scenario `unknown-user`

## Notes

- The response literal is intentionally identical to `RespondWrongPassword` to preserve the no-enumeration property.
