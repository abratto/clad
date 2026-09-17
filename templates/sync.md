<!-- Template for Stage 03 (03_syncs). Purpose & authoring rules: the stage 03 CONTEXT "Process" section and methodology/architecture/SYNCHRONIZATIONS.md §"Naming". This file is the output shape only. -->

sync When<TriggerConcept><TriggerAction><TriggerCompletion>Then<TargetConcept><TargetAction>[For<Scope>]

> Sync template. Declarative only — no branching, no state, no I/O.

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
```

Optional: a `when` may **constrain trigger input values** (input matcher,
R15): `Web/request: [ route: "profile" ] => [ routed ]`. Every constrained
key must be present with the equal value for the sync to fire. Use it for
route scoping on shared triggers; `Guard` stays for non-literal
comparisons. The rule block:

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

**Joins (multi-`when`).** A sync may declare several named conjuncts; it
fires once when every conjunct has completed in the same flow (order
independent). The first conjunct is the primary. Bind a conjunct's
completion or input as `name.field` / `name.param`:

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
`<Target><Action>[For<Scope>]WhenJoin<C1><A1><Out1>And<C2><A2><Out2>…` in
declared conjunct order — e.g.
`RespondWhenJoinListListedAndTagTagged`.

**Aggregation (`collect`).** The declarative analogue of `collectAs` —
gather a source's values into **one `List` value** (no filters, no JSON, R3):

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

## Cites

> Which use-case scenario(s) this sync exists to satisfy.

- `../01_usecase/output/usecase.md` — scenario "<name>"
  (cite the scenario by its **display name** exactly as written in usecase.md's `### Scenario:` heading — not the slug; a slug-mismatch fails `verify_scenario_coverage` at Stage 03)

## Notes

> Optional. Anything a reviewer should know.
