# Dependency review — `Web`

## Section 1 — Invocations received

| Action | Flow (sync) | Data received | Pattern | Source |
|---|---|---|---|---|
| `respond` | `LoginGrantsSession` (`successful-login`) | `status: 200`, `body: { sessionId }` | C + B | C: `200` literal; B: `sessionId` from `result_of(Session.grant).sessionId` (same flow) |
| `respond` | `LockoutOnFailedAttempts` (`lockout`) | `status: 401`, `body: { message: "too many attempts. try again in 15 minutes." }` | C | Both literal — pattern C constants baked into the sync |

> `Web.handle` is the trigger of every flow, never a `then` target;
> it does not appear in this section.

## Section 2 — Named-region reads by others (inbound Pattern D)

None — `Web` has no named region for other concepts to read.
Its state is implicitly the in-flight HTTP request, owned by the
runtime.

## Inconsistencies and risks

- `Web` carries inline routing logic for the `wrong-password`,
  `unknown-user`, and `wrong-password` chains (translating non-`Ok`
  outcomes from `User.lookupByUsername` and `PasswordAuth.check`
  into 401 responses). This is permitted by R4 (Web is the bootstrap)
  but means `Web`'s spec is the place where those failure-branch
  responses are pinned down — not Stage 03.

## Cross-checks

- `respond` is the canonical Web action (no Web concept spec; see
  [`../../../../methodology/architecture/WEB_CONCEPT.md`](../../../../methodology/architecture/WEB_CONCEPT.md)).

---

**Do you agree with this card? Any corrections before I continue?**
