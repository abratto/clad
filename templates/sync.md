<!-- Template for Stage 03 (03_syncs). Purpose: see methodology/architecture/SYNCHRONIZATIONS.md. -->

sync When<TriggerConcept><TriggerAction><TriggerCompletion>Then<TargetConcept><TargetAction>[For<Scope>]

> Sync template. Declarative only — no branching, no state, no I/O.

<!-- Naming rule

The sync name and file stem MUST read as a compressed rule:

  When<TriggerConcept><TriggerAction><TriggerCompletion>Then<TargetConcept><TargetAction>[For<Scope>]

Derive the trigger and target parts from the first `when` and `then`
signatures. Derive TriggerCompletion from the first token on the right
side of the `when` arrow. For `[ ok ; userId: ?u ]`, use `Ok`; for
`[ error: "notFound" ]`, use `NotFound`; for `[ refused ]`, use
`Refused`. Use PascalCase here; profile implementations lower this same
stem mechanically (Java class name = PascalCase stem, Java syncName() =
lower camel case stem).
-->

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `<#>` | `<#>` | `<Concept>/<action>: [...] => [ <outcome> ]` | `<Concept>/<action>: [ <arg>: <value> ; ... ]` | `<none \/ 200 / "message" / ...>` |

<!-- ⚠️ SYNC AUTHORING RULES — READ BEFORE WRITING THE RULE BLOCK

ONE SYNC PER CHAIN-TABLE ROW
  Each row transition in the approved chain table becomes exactly one sync
  file. Do not collapse multiple transitions into one sync. Count the rows
  in 02b_chain-table/output/ for this scenario; you must produce that many
  syncs (minus the Web/handle row, which is the entry point, not a sync
  trigger — unless Web/handle itself is the `when`).

WHERE CLAUSE — DECLARATIVE QUERIES ONLY
  The `where` clause uses paper-style declarative syntax. It is a query
  language, not a computation engine.

  ALLOWED:
    bind ( uuid() as ?newId )                         (identifier minting)
    User: { ?user email: ?email }                      (concept-state read — Pattern D)
    OPTIONAL { Tag: { ?article tag: ?tag } }           (conditional read)
    BIND ( ?article AS ?_eachthen )                    (aggregation grouping)

  NOT ALLOWED:
    if ?role = "admin"                                 (business branching)
    passwordHash = hash(body.password)                  (computation — belongs in concept)
    token        = jwt.sign(payload)                    (I/O — belongs in concept)
    summary      = toJson(result.items)                 (reshaping — belongs in concept)

  Computation, I/O, and business decisions belong in concept action
  outcomes. If you find yourself writing a function call in `where`, stop.
  The computation belongs inside the concept action that receives the data.

LITERAL LOCK
  Copy literals and signature tokens exactly from the approved Stage 02b
  row and Stage 02 concept signature.

  REQUIRED:
    Web/respond: [ status: 409 ; body: { reason: "on-loan" } ]

  NOT ALLOWED:
    Web/respond: [ status: "409" ; body: { reason: "OnLoan" } ]

NO INVENTED PAYLOAD FIELDS
  Response bodies and downstream calls may use only:
  - constants explicitly present in the target chain row
  - fields explicitly emitted by an earlier approved action outcome and
    declared in `where`
  - bindings from the `when` clause's ?variables

DECLARE BEFORE USE
  Every variable referenced in the `then` clause must either come directly
  from the `when` outcome's flow token or be declared explicitly in a
  `where` line. You may not reference a name in `then` that does not
  appear in `when` or `where`.

UPSTREAM CONTRACT CHECK
  If a needed name does not appear in the approved Stage 02b trigger token
  or concept outcome, stop and reopen Stage 02b. Stage 03 must not invent
  a source by reading `body.*`, `request.*`, or another undeclared payload
  path.
-->

## Rule

```
when {
    <Concept>/<action>: [ <param>: ?<var> ; ... ] => [ <output>: ?<var> ]
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

## Where clause patterns (for Stage 03a audit)

| Binding | Pattern | Source |
|---|---|---|
| `?<var>` | A | Trigger token (`when` clause) |
| `?<var>` | B | Flow-sibling output |
| `<literal>` | C | Sync constant |
| `<Concept>: { ... }` | D | Concept-state read |

## Cites

> Which use-case scenario(s) this sync exists to satisfy.

- `../01_usecase/output/usecase.md` — scenario "<name>"

## Notes

> Optional. Anything a reviewer should know.
