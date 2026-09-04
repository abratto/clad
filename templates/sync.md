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
