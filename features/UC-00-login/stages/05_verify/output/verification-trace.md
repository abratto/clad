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
3. `Session.grant { userId: U, sessionId: S, outcome: GRANTED }` — authorised by sync `LoginGrantsSession` (matches `PasswordAuth.check → OK`).

Response: `200 { sessionToken: S }` — authorised by sync `LoginGrantsSession`'s `Web.respond` clause.

**Trace verdict:** matches `01_usecase/output/usecase.md` §`successful-login`. No unauthorised tokens.

## Scenario `wrong-password`

Predicted root: `Web.handle`.

Children:

1. `User.lookupByUsername { outcome: FOUND }`.
2. `PasswordAuth.check { outcome: BAD_PASSWORD }`.

Response: `401 { message: "username or password didn't match" }` — authorised by `Web` directly (no sync; see note in `LoginGrantsSession.sync.md`).

**Trace verdict:** matches use case. No unauthorised tokens.

## Scenario `unknown-user`

Predicted root: `Web.handle`.

Children:

1. `User.lookupByUsername { outcome: UNKNOWN }`.

Response: `401` with the **same message** as `wrong-password` (no enumeration leak; required by `_config/voice.md`).

**Trace verdict:** matches use case. No unauthorised tokens. The voice constraint is satisfied because `Web` selects the response body without branching on `outcome`.

## Scenario `lockout`

Pending — depends on the `LockoutOnFailedAttempts` sync, which is
spec-only this iteration. No trace until the sync ships.

## Findings

None at this iteration. (See `findings.md` if any future regen produces violations.)
