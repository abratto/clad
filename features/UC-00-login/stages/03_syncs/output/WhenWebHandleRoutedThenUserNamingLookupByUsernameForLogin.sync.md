sync WhenWebHandleRoutedThenUserNamingLookupByUsernameForLogin

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `1` | `2` | `Web/handle: [...] => [ routed ]` | `UserNaming/lookupByUsername: [ username: ?u ]` | `<none>` |

## Rule

when {
    Web/handle: [ method: "POST /login" ; username: ?u ; password: ?p ] => [ routed ]
}
then {
    UserNaming/lookupByUsername: [ username: ?u ]
}

## Where clause patterns (for Stage 03a audit)

| Binding | Pattern | Source |
|---|---|---|
| `?u` | A | Trigger token — `Web/handle` input |
| `?p` | A | Trigger token — `Web/handle` input |

## Cites

- `../01_usecase/output/usecase.md` — scenarios `successful-login`, `wrong-password`, `unknown-user`, `lockout`

## Notes

- This is the shared first transition for all four UC-00-login scenarios.
