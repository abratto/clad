# Pattern D summary — UC-00-login

## Pattern D reads

No Pattern D reads in this feature.

Every `where` clause across the two UC-00 syncs uses either:

- A trigger pattern variable (data already bound by the `when`
  clause — e.g. `userId` in `LoginGrantsSession`),
- Pattern B (a flow-sibling output — e.g. `sessionId` from
  `Session.grant` consumed by `Web.respond` in the same flow), or
- Pattern C (a literal constant — e.g. `status: 200` / `401`).

No sync reads another concept's named region. UC-00-login therefore
has **zero cross-concept state coupling at runtime**.

## Cross-flow inconsistencies

- None at the Pattern D level.
- Action-name discrepancies between sync specs and chain tables
  (`Session.open` vs `Session.grant`; `PasswordAuth.verify` vs
  `PasswordAuth.check`) are tracked on the per-concept cards. The
  chain tables are canonical.

## What this feeds

- **Stage 04a (ORM).** Because no Pattern D reads exist, no
  cross-concept field exposure is required. Each concept's ORM is
  scoped strictly to its own `state` section.
- **Stage 04b (spec).** Sync specs need only normalise the
  action-name discrepancies noted on the per-concept cards.
- **Stage 05 (verify).** Trace target list is empty for Pattern D;
  flow tests still cover the `successful-login` and `lockout` chains
  end-to-end.

---

**Do you agree with this summary? Any corrections before I continue?**
