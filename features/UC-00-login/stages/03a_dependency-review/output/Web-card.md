# Dependency review — `Web`

## Section 1 — Invocations received

| Action | Flow (sync) | Data received | Pattern | Source |
|---|---|---|---|---|
| `respond` | `WhenUserLookupByUsernameRefusedThenWebRespondForLogin` (`unknown-user`) | `status: 401`, `body: { message: "username or password didn't match" }` | C | Both literal — pattern C constants baked into the sync |
| `respond` | `WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin` (`wrong-password`) | `status: 401`, `body: { message: "username or password didn't match" }` | C | Both literal — pattern C constants baked into the sync |
| `respond` | `WhenPasswordAuthCheckLockedThenWebRespondForLogin` (`lockout`) | `status: 401`, `body: { message: "Too many attempts. Try again in 15 minutes." }` | C | Both literal — pattern C constants baked into the sync |
| `respond` | `WhenSessionGrantGrantedThenWebRespondForLogin` (`successful-login`) | `status: 200`, `body: { sessionToken: ?sid }` | C + B | C: `200` literal; B: `?sid` from `Session/grant` completion (same flow) |

> `Web/handle` is the trigger of every flow, never a `then` target;
> it does not appear in this section.

## Section 2 — Named-region reads by others (inbound Pattern D)

None — `Web` has no named region for other concepts to read.
Its state is implicitly the in-flight HTTP request, owned by the
runtime.

## Inconsistencies and risks

- None at this time. All UC-00 response branches are now represented as
  Stage 03 syncs, so `Web` remains a pure bootstrap boundary rather
  than a hidden coordination surface.

## Cross-checks

- `respond` is the canonical Web action (no Web concept spec; see
  [`../../../../../methodology/architecture/WEB_CONCEPT.md`](../../../../../methodology/architecture/WEB_CONCEPT.md)).
- All four response syncs named above exist under `../../03_syncs/output/`.

---

**Do you agree with this card? Any corrections before I continue?**
