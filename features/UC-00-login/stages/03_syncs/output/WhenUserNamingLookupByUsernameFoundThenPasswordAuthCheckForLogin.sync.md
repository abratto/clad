sync WhenUserNamingLookupByUsernameFoundThenPasswordAuthCheckForLogin

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `2` | `3b` | `UserNaming/lookupByUsername: [...] => [ found ; userId ]` | `PasswordAuth/check: [ userId: ?user ; password: ?pass ]` | `<none>` |

## Rule

when {
    UserNaming/lookupByUsername: [ username: ?u ] => [ found ; userId: ?user ]
}
then {
    PasswordAuth/check: [ userId: ?user ; password: ?p ]
}

## Where clause patterns (for Stage 03a audit)

| Binding | Pattern | Source |
|---|---|---|
| `?user` | B | Flow-sibling output — `UserNaming/lookupByUsername` completion |
| `?p` | A | Trigger token — `Web/handle` input (shared flow) |

## Cites

- `../01_usecase/output/usecase.md` — scenarios `successful-login`, `wrong-password`, `lockout`

## Notes

- `userId` is carried by the `UserNaming/lookupByUsername` completion; the raw password is rebound from the original request via shared flow token.
