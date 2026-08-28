# legible-storage

`FactStore`/`Region` implementations of the fire-after-commit engine's
storage SPI, proving the engine is storage-agnostic.

- **`JenaFactStore`** — a triplestore backend: one named graph per concept
  (`concept:<name>`); facts are `predicate(subject) = value` triples.
- **`RmapPostgresFactStore`** — a relational backend using **relation
  realization**: Halpin's Rmap derives one typed table per concept, with the
  individual identifier as primary key, one typed column per fact type
  (`TEXT`/`INTEGER`/`TIMESTAMP`), `DEFAULT` for resettable facts, and `UNIQUE`
  constraints from the fact model. `LoginSchemas` holds the UC-00-login
  schemas derived from the Stage 03b data models. String values round-trip
  through the SPI (integers as decimal strings, timestamps as epoch-millisecond
  strings). Mandatory roles are recorded as schema metadata but not emitted as
  `NOT NULL` — the engine's SPI writes facts one at a time, so a concept with
  several mandatory facts cannot satisfy a row-level `NOT NULL` atomically.
- **`PostgresFactStore`** — a lighter relational backend using **fact
  realization**: a single generic `fact(concept, subject, predicate, value)`
  relation (the SQL analog of RDF triples).

`StorageContractTest` runs the login feature against the generic and triplestore
backends; `RmapPostgresFactStoreTest` runs it against the Rmap-derived schema and
asserts the schema shape. See
`methodology/implementation/STORAGE_MAPPING.md` for the Rmap vs fact-realization
distinction.

## Running

```bash
# Postgres backends require Docker (Testcontainers)
mvn test -f reference-impl/pom.xml -pl legible-storage -am
```
