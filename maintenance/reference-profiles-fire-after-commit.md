<!-- Maintenance-route planning record. Copy to maintenance/<change-name>.md. -->
# Maintenance change — `reference-profiles-fire-after-commit`

> Platform change under `methodology/core/ITERATIVE_CHANGES.md`
> §"Platform maintenance changes" and R20. Reference profiles of the
> fire-after-commit engine, not a feature-UC change: outcomes, response
> shape, concept boundaries, sync rules, and observable action order are
> **preserved**.

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `reference-impl/java-plain` (new), `reference-impl/java-micronaut-postgres` (re-lowered), `reference-impl/java-legible` (unchanged), `reference-impl/legible-storage` (already on the new engine)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Ship the three-tier reference stack the fire-after-commit engine promised but only the in-memory profile delivered: (1) `java-plain` — a lean, zero-framework quick-start (engine + login only); (2) `java-micronaut-postgres` re-lowered from the legacy transactional engine onto the fire-after-commit engine with Micronaut transport, R-map-derived Postgres concept state via `legible-storage`, JOOQ imported for typed introspection, Flyway managing base DDL; (3) containerization of the re-lowered profile (Dockerfile, docker-compose, fly.toml for Fly.io).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | same 4 login scenarios, same status codes (200/401/422-per-sync), same field values as `java-legible`'s LoginFlowTest; proven by ported FlowTraceTest + LoginFlowTest |
| Action ordering and sync deduplication | `preserved` | same 7 `When…` sync rules; `causedBySync` lineage asserted by FlowTraceTest |
| Flow-token lineage | `preserved` | action log + `causedBySync` on the engine, invariant across FactStore backends (StorageContractTest) |
| Storage/retention semantics | `preserved` (deliberate enabler) | `PostgresFactStore`/`RmapPostgresFactStore` implement the engine's `FactStore` SPI; concept state now derived from Stage 03b data models via `RmapDeriver`/`RelationSchema` (legacy hand-written per-concept migrations retired; Flyway retains base DDL ownership) |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `reference-impl/README.md` profile map (java-plain quick-start; java-micronaut-postgres re-lowered; java-micronaut-jena remains the only legacy); per-profile READMEs; `CHANGELOG.md` |
| Profile configuration or deployment files | yes | `clad.properties` example settings gain java-plain / java-micronaut-postgres rows (comment-only; defaults unchanged); new Dockerfile/docker-compose/fly.toml in the re-lowered module |
| Engine/runtime implementation | no | `legible-engine` and `legible-storage` are reused, never modified |
| Profile tests | yes | java-plain gets the extracted test set; java-micronaut-postgres tests port onto the new engine (concept + flow + architecture) |
| UC artefact chain | no | no feature artefact changes; derived-repo `_config` guidance in `CONTEXT_MANIFEST.md` and profile READMEs only |

## Deliberate surface reduction (recorded, not silent)

The re-lowered `java-micronaut-postgres` trims its transport surface to the
UC contract. The legacy module's demo transports — `AuthController`
(register/sign-out over the legacy engine), `GraphQLController`
(graphql-java over the legacy engine) — are removed rather than ported:
they exercised legacy-engine mechanics, duplicate `/login` functionality,
and were not part of the login feature contract. Rollback of this record
restores them. The `api` DTO set and the debug surface are preserved.

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Plain profile green | unit | `mvn -pl java-plain -am test` | pass | reactor green; 4 test classes ported (concept, flow, flow-trace, concurrency) |
| Re-lowered profile green (Testcontainers) | unit + integration | `mvn -pl legible-storage,java-micronaut-postgres -am test` | pass | 16/16 green (8 concept, 5 architecture, 2 HTTP flow, 1 factory) |
| Storage-agnostic parity | contract | `legible-storage` `StorageContractTest` unchanged-green | pass | reactor green — same Concept/SyncRule code |
| Canonical gate | gate | `test.command` (verify_artefacts + reactor mvn test) | pass | full reactor BUILD SUCCESS |
| Container smoke | manual | `docker compose up --build` then POST /login × scenarios | pass | 200/{sessionToken}; 401 opaque (wrong-password, unknown-user); 401 lockout message; /api/dev/syncs lists 7 rules; /api/dev/stuck clean |
| Fly config parses | manual | TOML structure check | pass | app/region/services sections parse; compose config -q green |
| Docs links | gate | `quality-gate/verify_links.py` | pass | (re-run at commit) |

## Gates

### Design gate

The human reviewed the profile plan (module layout, R-map schema ownership,
manual-only container smoke, in-place re-lowering) and approved proceeding
before any code was written. Status above records `approved`.

### Evidence gate

Approved by the human after the full test matrix was presented (reactor green,
container smoke scenarios identical to the canonical contract, gate scripts green).

## Notes

- `java-micronaut-jena` remains the legacy transactional showcase,
  untouched; after the re-lowering, no new work should target it.
- Derived repos: the new profiles are the sanctioned quick-starts for
  "plain Java" and "Ports & Adapters + Postgres" stacks, deployable via
  docker-compose for tests and fly.toml to Fly.io. `java-legible` remains
  the canonical seed feature example (multi-feature sync model).
