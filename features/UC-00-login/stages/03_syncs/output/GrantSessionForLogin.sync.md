# GrantSessionForLogin — successful checks open a session

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `3b` | `4a` | `PasswordAuth.check[Ok]` | `Session.grant(userId)` | `<none>` |

## Rule

```
when:  PasswordAuth.check[Ok]
where: B: userId = result_of(PasswordAuth.check).userId
then:  Session.grant(userId)
```

## Cites

- `../01_usecase/output/usecase.md` — scenario `successful-login`

## Notes

- `userId` is rebound explicitly from the successful
	`PasswordAuth.check` completion so the sync satisfies the
	declare-before-use rule.
