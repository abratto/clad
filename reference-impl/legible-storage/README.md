# legible-storage

`FactStore`/`Region` implementations of the fire-after-commit engine's
storage SPI, proving the engine is storage-agnostic.

- **`JenaFactStore`** — a triplestore backend: one named graph per concept
  (`concept:<name>`); facts are `predicate(subject) = value` triples.
- **`PostgresFactStore`** — a relational backend: a single `fact` relation
  `(concept, subject, predicate, value)`; the `concept` column is the named
  region (R2).

`StorageContractTest` runs the same login feature (`LoginApp.create(factStore)`)
against both backends (plus the in-memory canonical) and asserts identical
SPI semantics and login outcomes.

## Running

```bash
# Postgres backend requires Docker (Testcontainers)
mvn test -f reference-impl/pom.xml -pl legible-storage -am
```
