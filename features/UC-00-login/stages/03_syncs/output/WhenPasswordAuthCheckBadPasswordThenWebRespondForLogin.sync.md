sync WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `3b` | `4b` | `PasswordAuth/check: [...] => [ badPassword ]` | `Web/respond: [ status: 401 ; body: { message: "username or password didn't match" } ]` | `401`, `"username or password didn't match"` |

## Rule

when {
    PasswordAuth/check: [ userId: ?user ; password: ?p ] => [ badPassword ]
}
then {
    Web/respond: [ status: 401 ; body: { message: "username or password didn't match" } ]
}

## Where clause patterns (for Stage 03a audit)

| Binding | Pattern | Source |
|---|---|---|
| `401` | C | Sync constant |
| `"username or password didn't match"` | C | Sync constant |

## Cites

- `../01_usecase/output/usecase.md` — scenario `wrong-password`

## Notes

- The response literal is intentionally identical to `WhenUserLookupByUsernameRefusedThenWebRespondForLogin` to preserve the no-enumeration property.
