sync RespondForLoginWhenGrantGranted

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `4a` | `5` | `Session/grant: [...] => [ granted ; sessionId ] ∧ requested: Web/request: [ route: "login" ; method: "POST" ] => [ Routed ]` | `Web/respond: [ status: 200 ; sessionToken: ?sid ]` | `200` |

## Rule

when {
    Session/grant: [ userId: ?user ] => [ granted ; sessionId: ?sid ]
    requested: Web/request: [ route: "login" ; method: "POST" ] => [ Routed ; ... ]
}
then {
    Web/respond: [ status: 200 ; sessionToken: ?sid ]
}

## Where clause patterns (for Stage 03a audit)

| Binding | Pattern | Source |
|---|---|---|
| `?sid` | B | Flow-sibling output — `Session/grant` completion |
| `200` | C | Sync constant |

## Cites

- `../01_usecase/output/usecase.md` — scenario `successful-login`

## Notes

- Pattern B binding: the response body reuses the session id emitted by `Session/grant` in the same flow.
