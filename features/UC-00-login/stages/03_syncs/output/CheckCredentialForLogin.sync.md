# CheckCredentialForLogin — found users proceed to credential verification

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `2` | `3b` | `User.lookupByUsername[Found(userId)]` | `PasswordAuth.check(userId, password)` | `<none>` |

## Rule

```
when:  User.lookupByUsername[Found(userId)]
where: A: password = body.password
then:  PasswordAuth.check(userId, password)
```

## Cites

- `../01_usecase/output/usecase.md` — scenarios `successful-login`, `wrong-password`, `lockout`

## Notes

- `userId` is carried by the `User.lookupByUsername` completion; only the raw password is rebound from the original request.
