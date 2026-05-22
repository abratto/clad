# RespondLoginSuccess — granted sessions return the 200 token response

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `4a` | `5` | `Session.grant[Granted(sessionId)]` | `Web.respond(status=200, body={ sessionToken: sessionId })` | `200` |

## Rule

```
when:  Session.grant[Granted(sessionId)]
where: B: sessionId = result_of(Session.grant).sessionId
then:  Web.respond(status=200, body={ sessionToken: sessionId })
```

## Cites

- `../01_usecase/output/usecase.md` — scenario `successful-login`

## Notes

- This is the UC-00 worked example's canonical Pattern B binding: the response body reuses the session id emitted by `Session.grant` in the same flow.