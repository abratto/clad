# LookupUserForLogin — route login requests to user lookup

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `1` | `2` | `Web.handle[Routed]` | `User.lookupByUsername(username)` | `<none>` |

## Rule

```
when:  Web.handle[Routed]
where: A: username = body.username
then:  User.lookupByUsername(username)
```

## Cites

- `../01_usecase/output/usecase.md` — scenarios `successful-login`, `wrong-password`, `unknown-user`, `lockout`

## Notes

- This is the shared first transition for all four UC-00-login scenarios.
