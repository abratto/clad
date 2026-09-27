# Maintenance change — jOOQ as the SQL interface + blocking adapter-test gate

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** java-micronaut, legible-storage, all (quality-gate/templates)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** two changes. (1) An adapter-surface feature must now carry
  a profile-specific end-to-end adapter test, enforced **blocking** at Stage 04c
  (presence) and Stage 05 (enabled) instead of an advisory warning, with a new
  template. (2) jOOQ becomes the SQL interface of the Postgres/R-map persistence
  stack (the runtime store no longer uses raw JDBC), and the durable profile is
  covered by a full-stack Testcontainers test that asserts the R-map schema,
  Flyway base, no cross-concept FK, and a jOOQ↔engine round-trip — plus a
  Docker-capable CI job.

## Mechanism

- **Adapter-test gate.** `quality-gate/verify_adapter_test.py#has_adapter_surface`
  detects an adapter surface from a `port-spec.md` inbound entry, a `Web`
  bootstrap in a chain table, or `Web` in the use case;
  `quality-gate/clad_stages.py#_adapter_test_requires` emits a skip sentinel for
  non-adapter features/profiles; the check is wired blocking at Stage 04c
  (presence; `@Disabled` allowed while red) and Stage 05 (`--require-enabled`).
  `templates/http-integration-test.java` is the derivation template.
- **jOOQ as the SQL interface.**
  `reference-impl/legible-storage/src/main/java/dev/legible/storage/RmapPostgresFactStore.java#RmapRegion`
  builds every read/write/clear/subjects/facts query through the jOOQ DSL over
  dynamic `Table`/`Field` identifiers (the R-map tables are derived at runtime,
  so generated classes cannot be used); `#createSchema` still executes the
  Rmap DDL, and `RmapDeriver` remains the single source of the table shape.
- **Durable coverage.**
  `reference-impl/java-micronaut/src/test/java/com/example/app/storage/postgres/RmapPostgresPersistenceIT.java#jooqWriteIsVisibleToTheEngineStore`
  proves the DDLDatabase-introspected jOOQ schema and the runtime DDL agree; the
  same class asserts Flyway history and no cross-concept FK;
  `LoginFlowTest.java#latestActionChain` now asserts the full HTTP→controller→
  Web→concepts/syncs→response flow-token chain.
- **CI.** `.github/workflows/ci.yml` gains a Docker-capable `postgres-verify`
  job running `mvn verify -pl legible-storage,java-micronaut -am
  -Dclad.storage=postgres`; the Docker-free `java-verify` job is unchanged.

## Contract impact

| Surface | Impact |
|---|---|
| Action outcomes / response contracts | preserved |
| Action ordering / sync dedup | preserved |
| Flow-token lineage | preserved (now asserted end-to-end in the reference) |
| Storage / retention semantics | **changed** — the Postgres R-map store's SQL interface is jOOQ; observable SPI semantics and table shape are unchanged (existing `RmapPostgresFactStoreTest` green) |
| Gate verdicts | **changed** — a declared adapter surface with no (enabled) end-to-end test now blocks at 04c/05 |

## Impact matrix

| Artefact | Changed? | What |
|---|---|---|
| Documentation | yes | CHANGELOG, 04c/05 stage contracts, template |
| Profile config / deployment | yes | CI workflow (`postgres-verify` job) |
| Engine / runtime impl | yes | `RmapPostgresFactStore` re-realised on jOOQ |
| Profile tests | yes | `RmapPostgresPersistenceIT`; flow-token assertions; display-name cleanup |
| UC artefact chain | yes | Stage 04c/05 adapter-test check |

## Test matrix

| Invariant | Level | Command | Status | Evidence |
|---|---|---|---|---|
| Adapter-test check: pass/fail/skip branches | unit | `python3 -m pytest quality-gate/tests/test_adapter_test.py -q` | pass | 5 tests |
| Full quality-gate suite | unit | `python3 -m pytest quality-gate/tests -q` | pass | 287 passed |
| Artefact pipeline | gate | `python3 quality-gate/verify_artefacts.py` | pass | intact |
| R-map store (jOOQ) SPI+typing+persistence | integration | `mvn -pl legible-storage -am test -Dtest=RmapPostgresFactStoreTest` | pass | 5 tests (Testcontainers) |
| Service persistence: Flyway + R-map shape + no-FK + jOOQ round-trip | integration | `mvn -pl java-micronaut -am test -Dclad.storage=postgres -Dtest=RmapPostgresPersistenceIT` | pass | 3 tests |
| Full durable reactor | integration | `mvn verify -pl legible-storage,java-micronaut -am -Dclad.storage=postgres` | pass | BUILD SUCCESS |
| Reference HTTP e2e flow-token chain | integration | same (java-micronaut `LoginFlowTest`) | pass | 2 tests |

## Gates

### Design gate

Approved by the operator in-session: presence at 04c + enabled at 05; both
targets for the e2e test; jOOQ as the runtime SQL interface; bundle as `0.15.0`;
maintenance record for the reference-impl changes.

### Evidence gate

Approved on the green quality-gate suite plus the Testcontainers-backed
`legible-storage`/`java-micronaut` runs above.

## Notes

- A full `RmapPostgresFactStore`-against-`StorageContractTest` subclass was
  considered and **deliberately not added**: `StorageContractTest` is
  set-valued (`readWriteRemoveClear` expects `{v1, v2}` for one predicate), while
  the R-map store is functional (one value per fact type per subject). Forcing it
  would require a set-valued column model the R-map does not have; its focused
  test plus the full-stack IT are the correct coverage.
- Agent must not create/push the `v0.15.0` tag; the human does (AGENTS §2.16).
