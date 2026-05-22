# RespondLocked — locked accounts return the lockout 401 response

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `3b` | `4c` | `PasswordAuth.check[Locked]` | `Web.respond(status=401, body={ message: "Too many attempts. Try again in 15 minutes." })` | `401`, `"Too many attempts. Try again in 15 minutes."` |

## Rule

```
when:  PasswordAuth.check[Locked]
then:  Web.respond(status=401, body={ message: "Too many attempts. Try again in 15 minutes." })
```

## Cites

- `../01_usecase/output/usecase.md` — scenario `lockout`

## Notes

- Unlike `wrong-password` and `unknown-user`, the lockout state is intentionally visible to the user.
