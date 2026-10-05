# Maintenance change — `relational-gaps-closure`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed` (`draft` until design approval, `active` while
  implementing, `closed` after evidence approval)
- **Affected profile(s):** `reference-impl/legible-storage`;
  doctrine/contract docs (`methodology/architecture/DATA_MODEL_NOTES.md`,
  `methodology/implementation/STORAGE_MAPPING.md`,
  `reference-impl/java-micronaut/RELATIONAL_LOWERING.md`)
- **Feature-contract impact:** `preserved` (no use-case outcome, response, or
  flow-token change; login-derived schema byte-identical)
- **Design gate:** `approved` (human, in-conversation: "address the findings" —
  three resolutions approved as proposed in the domain-exercise report)
- **Evidence gate:** `approved`
- **Change summary:** Close the three design gaps the domain exercise pinned:
  (1) render intra-concept foreign keys and make the separate-subtype base-row
  requirement a loud FK failure instead of silent divergence; (2) guard
  partition's unroutable predicate at region creation instead of the
  silent-wrong-table behavior; (3) extend the machine-model grammar with
  filtered uniqueness (`unique while <field> absent`) realised as a Postgres
  partial unique index, so history-preserving 1:1 facts are expressible.

## Mechanism

- **FK rendering** — `dev.legible.storage.RelationSchema#ddl` and
  `dev.legible.storage.RmapMigration#createTable` render each
  `foreignKeys` entry (`col -> table(target)`) as
  `FOREIGN KEY ("col") REFERENCES "table" ("target")`. The child-table FK's
  parent was malformed (`order(order_intake)` — the concept name as the target
  column); `RmapDeriver#childTables` now names the actual subject table/column
  (`order_intake(order)`) via the model's table-name map.
- **Separate-subtype semantics** — no base-row materializer is added: with the
  FK rendered, writing a subtype fact for an individual with no supertype row
  fails loudly on the population constraint the fact model itself asserts
  (`Sub is a Sup`). Production actions that must create a subtype individual
  write the supertype's facts in the same buffered action, or an earlier one.
- **Partition guard** —
  `dev.legible.storage.RmapPostgresFactStore.RmapRegion`'s constructor counts
  the tables owning each fact predicate; anything owned by more than one table
  (only partition flattening can produce that) throws at region creation,
  naming the predicates and the model remediation. Derivation still realises
  partition for documentation/spec purposes; the runtime refuses routing it
  cannot answer.
- **Filtered uniqueness** — `RmapDeriver` extracts
  `-- unique while <field> (absent|missing)` annotations
  (`FactType#uniqueWhileAbsent`); `RelationSchema.Column` carries
  `uniqueWhileAbsent`; the DDL renderers append
  `CREATE UNIQUE INDEX IF NOT EXISTS "<table>_<col>_open_idx"
  ON "<table>" ("<col>") WHERE "<field_column>" IS NULL` per filtered column —
  the Postgres realisation of external uniqueness restricted to open
  individuals. The in-memory store does not enforce it (documented).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Login flows unchanged; `V1__login_rmap.sql` byte-identical (no filtered/unique-multi/subtype facts in UC-00). |
| Action ordering and sync deduplication | `preserved` | No engine change. |
| Flow-token lineage | `preserved` | Flow log untouched. |
| Storage/retention semantics | `preserved` (extended) | Partition models now fail loudly at region creation; subtype populations enforced by the fact model's own subset constraint. Domain fixtures/probes updated accordingly. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `DATA_MODEL_NOTES.md` (filtered-uniqueness annotation), `RELATIONAL_LOWERING.md` (guard, FK rendering, filtered-unique row + subtype-write semantics), `STORAGE_MAPPING.md` (FK rendering true). |
| Profile configuration or deployment files | no | No config keys changed. |
| Engine/runtime implementation | yes | `legible-storage` only: `RmapDeriver` (parse, child FK, addColumn), `RelationSchema` (`Column.uniqueWhileAbsent`, `ddl()` FK + filtered index), `RmapMigration` (same rendering), `RmapPostgresFactStore` (partition guard). |
| Profile tests | yes | Domain oracles re-frozen; probes P1/P3/P4 rewritten; new unit tests for filter parsing. |
| UC artefact chain | no | `## State` unchanged for shipped examples. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Filtered-unique annotations parse and reach the Column model | unit | `RmapDeriverModelTest#filteredUniquenessCarries…` | pass | `uniqueWhileAbsent` carried; the filtered form *replaces* the plain `UNIQUE` (no column-level UNIQUE fires) |
| Child-table FK names the subject's own table/column | unit | `RmapDeriverModelTest#childTableForeignKeys…` + re-frozen ordering oracle | pass | `order -> intake(order)`; dropped when the parent is identity-only |
| Intra-concept FKs render in both DDL writers | integration (Testcontainers) | domain oracles + `createSchema()` | pass | registry FK in oracle; schema applies on Postgres |
| Subtype write without a supertype row fails loudly (FK) | integration | `RmapEdgeBehaviorTest#separateSubtypePopulationIsEnforcedByTheFk` | pass | violation names `patient_registry__person`; base+subtype writes join |
| Partition routing ambiguity fails at region creation | integration | `RmapEdgeBehaviorTest#partitionRoutingIsRefusedAtRegionCreation` | pass | guard names `partyName` + remediation; optional variant refused too |
| Filtered uniqueness preserves loan history; plain `unique` blocks it | integration | `RmapEdgeBehaviorTest#filteredUniquenessPreservesLoanHistory` | pass | open-conflict on `open_idx`; after return l-2 succeeds (history); plain-unique contrast blocks |
| Login migration stays byte-identical | drift guard | `RmapMigrationTest` | pass | green without regeneration |
| Reactor + gates green | gate | `test.command`, pytest, postgres reactor | pass | reactor 41/47/**65**/21 + java-micronaut 21 BUILD SUCCESS under `-Dclad.storage=postgres`; `test.command` exit 0; pytest 313 passed; `verify_artefacts` intact |

## Gates

### Design gate

Approved in-conversation (2026-10-04). Three decisions: render intra-concept
FKs with no base-row materializer (loud subset enforcement); refuse partition
routing at region creation (derivation still renders the schema); add
`unique while <field> absent` to the machine-model block, realised as a
Postgres partial unique index, closing the 1:1/history deferral with the
lending domain as its worked example.

### Evidence gate

Approved — the matrix above is the evidence: postgres reactor
41/47/65/21 BUILD SUCCESS (`-Dclad.storage=postgres`), the login drift guard
byte-identical without regeneration, `test.command` exit 0, pytest 313 passed,
`verify_artefacts` intact, and each rewritten probe (P1 loud FK, P3 partition
guard, P4 filtered-uniqueness history preserved) green on Postgres.

## Notes

- Compatibility: `Column`/`FactType` records gain components; equality is only
  compared between same-deriver outputs (LoginSchemas oracle stays valid).
  jOOQ's `DDLDatabase` (H2) may not parse the partial unique index — the login
  migration carries none, and a derived app that adopts filtered uniqueness
  with DDLDatabase codegen must re-verify its codegen step (documented in
  `RELATIONAL_LOWERING.md`).
- The in-memory lifecycle does not enforce filtered uniqueness or FKs; enforcement
  is profile-level (Postgres), consistent with the durable contract.
- Rollback: revert the branch; previous behavior is pinned by the domain probes'
  history.
