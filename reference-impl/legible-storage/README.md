# legible-storage

`FactStore`/`Region` implementations of the fire-after-commit engine's
storage SPI, proving the engine is storage-agnostic. CLAD ships **in-memory**
(canonical, in `legible-engine`) and **Postgres** (here). Any other backend —
RDF/JSON-LD included — is a `FactStore` implementation you provide against the
SPI.

- **`RmapPostgresFactStore`** — the durable relational backend (**relation
  realization**): a concept region is a **table set** derived by Halpin's Rmap
  (`RmapDeriver`) from the Stage 03b data model's `## Machine model` block.
  Typed columns (`TEXT`/`INTEGER`/`TIMESTAMP`; instants as ISO-8601 strings),
  composite PKs for objectified subjects, child tables for multi-valued
  facts, `NOT NULL`/`UNIQUE`/`CHECK`/`DEFAULT`, rendered intra-concept
  `FOREIGN KEY`s and partial unique indexes for filtered uniqueness
  (`unique while <field> absent`). It implements `TransactionalRegion`, so a
  concept action's writes flush as one statement per individual — that is how
  Rmap's mandatory → `NOT NULL` is honoured. Severally guarded: a partitioned
  supertype's region is refused at creation; a subtype write without its
  supertype row fails loudly on the FK.
- **`PostgresFactStore`** — the light alternative (**fact realization**): a
  single generic `fact(concept, subject, predicate, value)` relation — the
  SQL analog of RDF triples; schema-free, no Rmap constraints.

**How the pipeline works**: see
[`methodology/architecture/RELATIONAL_RMAP.md`](../../methodology/architecture/RELATIONAL_RMAP.md)
for the end-to-end narrative (CSDP → machine model → Rmap → migration and
runtime), [`methodology/implementation/STORAGE_MAPPING.md`](../../methodology/implementation/STORAGE_MAPPING.md)
for the Rmap vs fact-realization doctrine, and
[`java-micronaut/RELATIONAL_LOWERING.md`](../java-micronaut/RELATIONAL_LOWERING.md)
for the per-clause lowering rules.

## Where the schema comes from

The derivation reads **data-model files**, not strings:
`LoginSchemas` derives the login trio from
`examples/UC-00-login/stages/03b_data-model/output/*.data-model.md`;
`RmapDeriverTest` asserts the machine-block derivation equals the `## State`
equivalence, and `RmapMigrationTest` (in the profile) drift-guards the
Flyway migration against a fresh render. Shape coverage beyond login lives in
`src/test/resources/domains/` (`clinic`, `ordering`, `lending`): per concept a
`## State`, the resolved data model, and a frozen migration oracle.

## Running

```bash
# Postgres backends and the domain suites require Docker (Testcontainers)
mvn test -f reference-impl/pom.xml -pl legible-storage -am -Dclad.storage=postgres

# Docker-free (LoginSchemas derivation + parity suites)
mvn test -f reference-impl/pom.xml -pl legible-storage -am
```

Key suites: `RmapDomainStorageTest` / `RmapDomainDerivationTest` (three
fixture domains), `RmapEdgeBehaviorTest` (P1–P5: loud FKs, CHECK rejection,
partition refusal, filtered uniqueness vs plain, retract shapes),
`RmapCompositeSubjectTest`, `RmapPostgresFactStoreTest`, `PostgresFactStoreTest`.
