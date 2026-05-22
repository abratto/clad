# RespondWrongPassword — bad credentials return the opaque 401 response

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `3b` | `4b` | `PasswordAuth.check[BadPassword]` | `Web.respond(status=401, body={ message: "username or password didn't match" })` | `401`, `"username or password didn't match"` |

## Rule

```
when:  PasswordAuth.check[BadPassword]
then:  Web.respond(status=401, body={ message: "username or password didn't match" })
```

## Cites

- `../01_usecase/output/usecase.md` — scenario `wrong-password`

## Notes

- The response literal is intentionally identical to `RespondUnknownUser` to preserve the no-enumeration property.
