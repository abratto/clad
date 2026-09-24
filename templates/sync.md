<!-- Template for Stage 03 (03_syncs). Purpose & authoring rules: the stage 03 CONTEXT "Process" section and methodology/architecture/SYNCHRONIZATIONS.md §"Naming". This file is the output shape only. -->

sync <TargetAction>[For<Route>]When<TriggerAction><TriggerCompletion>

> Sync template. Declarative only — no branching, no state, no I/O.

## The simple case (start here)

A sync is three clauses: `when` (what completed), `where` (optional bindings),
`then` (what to invoke). The most common shape is a **bootstrap row** — the
request triggers one concept action:

```
sync LookupByUsernameForLoginWhenRequestRouted

when {
    Web/request: [ route: "login" ; username: ?user ] => [ Routed ]
}
then {
    UserNaming/lookupByUsername: [ username: ?user ]
}
```

- `?user` is bound in `when` and used in `then` — internal flow data, no
  cross-concept read.
- The response side is the same three clauses, matching the concept's completion:
  `when { Session/grant: [ ... ] => [ Granted ; sessionToken: ?token ] } then { Web/respond: [ status: 200 ; sessionToken: ?token ] }`.
- When the row **mints** an entity, add `where { bind ( uuid() as ?<id> ) }`.
- Most chain-table rows need nothing more than this section. Read on only when
  your row needs a join, a pin, a set, or an absence.

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `<#>` | `<#>` | `<Concept>/<action>: [...] => [ <outcome> ]` | `<Concept>/<action>: [ <arg>: <value> ; ... ]` | `<none \/ 200 / "message" / ...>` |

<!-- Authoring rules (one sync per chain-table row; `where` is a declarative
query not a computation engine; literal lock; no invented payload fields;
declare-before-use; reopen 01b/02 on contract drift) live in the stage 03
CONTEXT "Process" + "Semantic checks" and are not duplicated here. -->

## Rule

```
when {
    <Concept>/<action>: [ <param>: <requiredValue> ; ?<var> ; ... ] => [ <outcome> ]
}
where {
    bind ( <expr> as ?<var> )
    <Concept>: { ?<id> <field>: ?<var> ; ... }
    OPTIONAL { <Concept>: { ?<id> <field>: ?<var> } }
    BIND ( ?<var> AS ?_eachthen )
}
then {
    <Concept>/<action>: [ <param>: ?<var> ; ... ]
}
```

Optional: a `when` may **constrain trigger input values** (input matcher,
R15): `Web/request: [ route: "profile" ] => [ routed ]`. Every constrained
key must be present with the equal value for the sync to fire. Use it for
route scoping on shared triggers; `Guard` stays for non-literal
comparisons.

## Translating from paper / ConceptBox examples

> The WYSIWID paper and the paper authors' ConceptBox engine order and phrase
> things differently. Translating an example verbatim can produce a rule that
> fires with blank arguments or bypasses the audit. Four mappings:

- **Request-first (paper) / order-agnostic (`actions([...])`, ConceptBox) → pin last.** CLAD's engine evaluates a rule's `where` against its primary (**first**) conjunct, so the flow pin is the **final** conjunct; a pin placed first binds `triggerField`/`triggerInput` to the request instead of the domain trigger.
- **`frames.filter(...)` (ConceptBox) → a concept action outcome.** Business discrimination belongs in the concept (R3); CLAD has no in-`where` filter.
- **`collectAs` (ConceptBox) → `collect` / `collect by ?key`** for a single binding; a correlated multi-binding record (several bindings per frame) has no declarative CLAD form today.
- **Nested `body:` in `then` (paper / ConceptBox) → the primary adapter.** The sync carries the authored result, not the wire frame; `verify_sync_then_shape.py` enforces the flat `then`.

## When you need more

### Joins (multi-`when`)

A sync may declare several named conjuncts; it fires once when every conjunct
has completed in the same flow (order independent). The first conjunct is the
primary. Bind a conjunct's completion or input as `name.field` / `name.param`:

```
when {
    a: Catalog/list: [ id: ?id ] => [ Listed ; id: ?id ]
    b: Tagging/tag: [ id: ?id ] => [ Tagged ; id: ?id ]
}
then {
    Web/respond: [ listed: ?id ]
}
```

A single *unnamed* conjunct keeps the classic form (and naming) unchanged.
The joined stem is
`<TargetAction>[For<Route>]WhenJoin<C1><A1><Out1>And<C2><A2><Out2>…` in
declared conjunct order — e.g.
`RespondWhenJoinListListedAndTagTagged`.

### Route-scoped bootstraps carry their route

A rule whose `when` matches a `Web/request` route is named
`<TargetAction>For<Route>When<TriggerAction><Completion>` —
`VerifyForReturnsWhenRequestRouted`. Two use cases may bootstrap the same
target action on different routes, and nothing else in the name separates them.

### Flow pinning (every non-bootstrap rule)

A rule whose `when` is not a lone `Web/request` names its flow root —
`Web/request` with its route — as its **last** conjunct, so it can only fire in
its own flow:

```
when {
    closed: Lending/close: [ ... ] => [ Returned ; ... ]
    requested: Web/request: [ route: "returns" ] => [ Routed ; ... ]
}
```

Last, not first: the engine evaluates a rule's `where` with its primary (first)
conjunct, and `triggerField`/`triggerInput` read the completion/input of that
primary — a pin first would bind them to the request, not the domain trigger.
The pin **conjunct** is not part of the name (it is in every rule, so it
discriminates nothing); a rule that must fire in two flows is two rules. Its
**route is** a name component: a pinned rule's name carries `For<Route>` too, so
two use cases that pin the same trigger and target on different routes register
distinct names. See `maintenance/sync-flow-pinning.md` and
`maintenance/route-scoped-pinned-names.md`.

### Absence (`absent`)

The negative state pattern — keep the frame only if the subject has **no** such
value (a D&minus; read: it binds nothing):

```
where {
    fanOut ( ?loanId ; "Lending" ; "borrower" ; ?memberId )
    absent ( "Lending" ; ?loanId ; "returnedAt" )
    collect ( ?loanId as ?openLoans )
}
```

Not a filter: no computation, no JSON, an absence only (R3). It fails closed on
an unbound subject, and a `where` that ends with no frames does not fire — so an
aggregate over a possibly-empty set uses `collectBy`, not `collect`.

### Aggregation (`collect`)

The declarative analogue of `collectAs` — gather a source's values into **one
`List` value** (no filters, no JSON, R3):

```
where {
    collect ( <source> as ?<var> )
    collect distinct ( <source> as ?<var> )       // de-duplicated + ordered
    collect by ?<groupKey> ( <source> as ?<var> ) // one List per group
}
```

This is *not* the declined imperative `frames.query/filter/collectAs`:
`collect` only gathers values a declarative source already produces.

## Where clause patterns (for Stage 03a audit)

| Binding | Pattern | Source |
|---|---|---|
| `?<var>` | A | Trigger token (`when` clause) |
| `?<var>` | B | Flow-sibling output |
| `<literal>` | C | Sync constant |
| `<Concept>: { ... }` | D | Concept-state read |

**A/B vs. D — the one choice that matters:** reuse a flow binding (A/B) when the
value already travelled this flow; read concept state (D) only when the value was
never in this flow. D is a real cross-boundary read and the Stage 03a audit will
flag it.

## Cites

> Which use-case scenario(s) this sync exists to satisfy.

- `../01_usecase/output/usecase.md` — scenario "<name>"
  (cite the scenario by its **display name** exactly as written in usecase.md's `### Scenario:` heading — not the slug; a slug-mismatch fails `verify_scenario_coverage` at Stage 03)

## Notes

> Optional. Anything a reviewer should know.
