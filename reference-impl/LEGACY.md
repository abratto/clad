# Retired legacy stack (RDF/SPARQL / Jena)

The original **transactional-predicate engine** and its RDF/SPARQL profile
were retired from CLAD. They were:

- `reference-impl/clad-engine/` — the `dev.clad.engine` coordination engine
  (`ActionLog`, `ConceptAgent`, `SyncAgent`, `SyncDispatcher`, `FlowManager`,
  `Storage`).
- `reference-impl/java-micronaut-jena/` — the Java 21 + Micronaut + Apache
  Jena profile built on it.

They are **no longer part of the build, CI, or any quality-gate check**, and
they receive no maintenance. The canonical engine is the fire-after-commit
[`legible-engine/`](legible-engine/); the durable profile is
[`java-micronaut/`](java-micronaut/).

## Where to find it

The last CLAD version that contains the stack is tag **`v0.4.0`**. To inspect
it:

```bash
git show v0.4.0:reference-impl/java-micronaut-jena/README.md
git checkout v0.4.0 -- reference-impl/clad-engine reference-impl/java-micronaut-jena
```

## Why it was retired

The engine encoded the older "sync-as-transaction" reading of Jackson's *The
Essence of Software* (atomic composite writes with rollback). The
fire-after-commit engine replaced it — coordination happens after an action is
committed to a per-flow action log, failures are named outcomes rather than
rollbacks, and storage is a `FactStore`/`Region` detail. See
[`README.md`](README.md) §"Why the engine was re-architected".

The retirement and the accompanying simplifications are recorded in
`maintenance/clad-simplification-and-legacy-retirement.md` and `CHANGELOG.md`.
