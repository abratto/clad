<!-- Template for Stage 03 (03_syncs). Purpose: see methodology/architecture/SYNCHRONIZATIONS.md. -->

# <SyncName> — <one-line purpose>

> Sync template. Declarative only — no branching, no state, no I/O.

## Rule

```
when:  <Concept>.<action>(<args>) -> <Outcome>
where: <local> = <pure expression>
       <local> = <pure expression>
then:  <Concept>.<action>(<args>)
       <Concept>.<action>(<args>)
```

## Cites

> Which use-case scenario(s) this sync exists to satisfy.

- `../01_usecase/output/usecase.md` — scenario "<name>"

## Notes

> Optional. Anything a reviewer should know.
