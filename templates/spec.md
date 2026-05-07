<!-- Template for Stage 04b (04b_spec). Purpose: see methodology/implementation/STAGES.md §"Stage 04b — Spec". -->

# `<ConceptName>` — SPEC

> A SPEC is the contract slice of a concept that the implementation
> compiles against. It is derived mechanically from
> `<ConceptName>.concept.md`: action signatures, outcome enums, and
> flow-token shape — nothing else. No prose principle, no edge-case
> discussion; that lives in the concept spec.

## Action signatures

```
<actionName>(<arg>: <Type>, …) -> <Outcome1> | <Outcome2> | …
<actionName>(<arg>: <Type>, …) -> <Outcome> | …
```

## Outcome enums

```
<actionName>:
  - <Outcome1>(<payload-shape>?)
  - <Outcome2>(<payload-shape>?)
```

## Flow-token shape

For each action, the fields the emitted flow token must carry, in
addition to the standard envelope (`id`, `parent`, `actor`, `at`,
`outcome`):

```
<actionName>: { <field>: <Type>, <field>: <Type> }
```

## Notes

> Optional. Mark anything the implementer must know that is not
> obvious from the signatures (e.g. an outcome that must be returned
> within a deadline).
