sync WhenPasswordAuthCheckOkThenSessionGrantForLogin

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `3b` | `4a` | `PasswordAuth/check: [...] => [ ok ; userId ]` | `Session/grant: [ userId: ?user ]` | `<none>` |

## Rule

when {
    PasswordAuth/check: [ userId: ?user ; password: ?p ] => [ ok ; userId: ?user ]
}
then {
    Session/grant: [ userId: ?user ]
}

## Where clause patterns (for Stage 03a audit)

| Binding | Pattern | Source |
|---|---|---|
| `?user` | B | Flow-sibling output — `PasswordAuth/check` completion |

## Cites

- `../01_usecase/output/usecase.md` — scenario `successful-login`

## Notes

- `userId` is rebound from the successful `PasswordAuth/check` completion.
