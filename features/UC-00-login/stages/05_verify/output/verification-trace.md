# Verification trace — UC-00-login

> **Status: spec-only.** The Java profile is scaffolding (no real
> HTTP handler, no live test run); this trace is the **predicted**
> walk derived from the use case, syncs, and SPECs. When the flow
> tests in `04c` go green, this file will be regenerated from the
> actual `ActionLog` contents.

## Scenario `successful-login`

Predicted root: `Web.handle { requestId: r1 }` (parent: none).

Children (in order, all parented to the root):

1. `User.lookupByUsername { username: "ada", userId: U, outcome: FOUND }` — authorised by `User.spec.md`.
2. `PasswordAuth.check { userId: U, outcome: OK }` — authorised by `PasswordAuth.spec.md`.
3. `Session.grant { userId: U, sessionId: S, outcome: GRANTED }` — authorised by sync `GrantSessionForLogin`.

Response: `200 { sessionToken: S }` — authorised by sync `RespondLoginSuccess`.

**Trace verdict:** matches `01_usecase/output/usecase.md` §`successful-login`. No unauthorised tokens.

## Scenario `wrong-password`

Predicted root: `Web.handle`.

Children:

1. `User.lookupByUsername { outcome: FOUND }`.
2. `PasswordAuth.check { outcome: BAD_PASSWORD }`.

Response: `401 { message: "username or password didn't match" }` — authorised by sync `RespondWrongPassword`.

**Trace verdict:** matches use case. No unauthorised tokens.

## Scenario `unknown-user`

Predicted root: `Web.handle`.

Children:

1. `User.lookupByUsername { outcome: NOT_FOUND }`.

Response: `401` with the **same message** as `wrong-password` (no enumeration leak; required by `_config/voice.md`) — authorised by sync `RespondUnknownUser`.

**Trace verdict:** matches use case. No unauthorised tokens. The voice constraint is satisfied because both 401 branches converge on the same approved response literal.

## Scenario `lockout`

Predicted root: `Web.handle`.

Children:

1. `User.lookupByUsername { outcome: FOUND }`.
2. `PasswordAuth.check { outcome: LOCKED }`.

Response: `401 { message: "Too many attempts. Try again in 15 minutes." }` — authorised by sync `RespondLocked`.

**Trace verdict:** matches use case. No unauthorised tokens.

## Findings

None at this iteration. (See `findings.md` if any future regen produces violations.)
