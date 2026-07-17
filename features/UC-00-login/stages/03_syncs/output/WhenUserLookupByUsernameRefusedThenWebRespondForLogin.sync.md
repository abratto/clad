sync WhenUserLookupByUsernameRefusedThenWebRespondForLogin

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `2` | `3a` | `User/lookupByUsername: [...] => [ refused ]` | `Web/respond: [ status: 401 ; body: { message: "username or password didn't match" } ]` | `401`, `"username or password didn't match"` |

## Rule

when {
    User/lookupByUsername: [ username: ?u ] => [ refused ]
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

- `../01_usecase/output/usecase.md` — scenario `unknown-user`

## Notes

- The response literal is intentionally identical to `WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin` to preserve the no-enumeration property.
