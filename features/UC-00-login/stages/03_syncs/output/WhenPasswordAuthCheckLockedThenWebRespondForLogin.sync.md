sync WhenPasswordAuthCheckLockedThenWebRespondForLogin

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `3b` | `4c` | `PasswordAuth/check: [...] => [ locked ]` | `Web/respond: [ status: 401 ; body: { message: "Too many attempts. Try again in 15 minutes." } ]` | `401`, `"Too many attempts. Try again in 15 minutes."` |

## Rule

when {
    PasswordAuth/check: [ userId: ?user ; password: ?p ] => [ locked ]
}
then {
    Web/respond: [ status: 401 ; body: { message: "Too many attempts. Try again in 15 minutes." } ]
}

## Where clause patterns (for Stage 03a audit)

| Binding | Pattern | Source |
|---|---|---|
| `401` | C | Sync constant |
| `"Too many attempts. Try again in 15 minutes."` | C | Sync constant |

## Cites

- `../01_usecase/output/usecase.md` — scenario `lockout`

## Notes

- Unlike `wrong-password` and `unknown-user`, the lockout state is intentionally visible to the user.
