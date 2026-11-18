# Maintenance change — `rmap-richer-constraints`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed` (`draft` until design approval, `active` while
  implementing, `closed` after evidence approval)
- **Affected profile(s):** `quality-gate/rmap.py`,
  `quality-gate/artifact_parsers.py`, `quality-gate/generate_data_model.py`,
  `quality-gate/verify_data_model.py`, `reference-impl/legible-storage`;
  architecture/implementation docs and the Stage 03b template.
- **Feature-contract impact:** `preserved` (no login action outcome, response
  contract, or flow-token change; the shipped login schema stays byte-identical)
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Extend the conceptual-model block with role-level
  participation, multi-column uniqueness, and subtype disjoint/exhaustive /
  discriminator declarations; realize them in the Rmap supported subset.
- **Dependent re-entry:** none

## Mechanism

- **Role-level participation.** Fact annotations gain `value mandatory` and
  `value optional` alongside the existing subject `mandatory`/`optional`.
  `artifact_parsers.role_flags` is the shared parser. A 1:1 fact between two
  object types is legal only when the author has oriented it on the mandatory
  side; the deriver validates the choice and rejects the optional-side
  orientation. Automatic predicate re-orientation (flipping subject/value in
  the runtime) is explicitly deferred: it needs a runtime fact-mapping change,
  not just a DDL change.
- **Multi-column uniqueness.** `unique ( p1, p2, ... )` (optionally
  `while p3 absent`) declares a table-level uniqueness constraint. The deriver
  resolves every predicate to one table, renders `UNIQUE (...)`, or a partial
  unique index for the filtered form; cross-table and multi-valued predicates
  fail loudly.
- **Subtype completeness.** `disjoint ( A, B, ... )` and `exhaustive ( Sup )`
  declare set constraints. `absorb` subtypes may add
  `discriminator <predicate> = <value>`; membership becomes explicit and the
  generated check ties the discriminator to the subtype's mandatory facts.
  Disjointness is enforced for absorbed subtypes via a pairwise check (or is
  implied by distinct discriminator values). Partition disjointness is
  structural; separate-table disjointness/exhaustiveness and cross-table
  exhaustiveness are declared/validated but not DB-enforced, and the deriver
  reports that honestly.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Login models use none of the new syntax; their derived schema/descriptor must stay byte-identical. |
| Action ordering and sync deduplication | `preserved` | No engine or sync change. |
| Flow-token lineage | `preserved` | Flow log untouched. |
| Storage/retention semantics | `changed` | Derived apps can add role constraints, multi-column unique keys, and explicit subtype membership/checks. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `RMAP_CONFORMANCE.md`, `DATA_MODEL_NOTES.md`, `RELATIONAL_RMAP.md`, `RELATIONAL_LOWERING.md`, `CITATIONS.md` if needed. |
| Profile configuration or deployment files | no | No config keys changed. |
| Engine/runtime implementation | no | Mapper/parser/verifier only; the runtime consumes the generated DDL/descriptor. |
| Profile tests | yes | New unit tests, generator/fidelity tests, and Postgres population probes. |
| UC artefact chain | no | Frozen login models and examples are unchanged. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Role annotations parse and wrong 1:1 orientation is rejected | unit | parser + conformance tests | pass | `RoleParticipationConformanceTests`, `test_role_flags…` |
| Multi-column unique renders a table constraint and a filtered partial index | unit | Rmap conformance tests | pass | `MultiColumnUniqueConformanceTests` |
| Cross-table / multi-valued unique groups fail loudly | unit | Rmap conformance tests | pass | `test_cross_table_unique_is_rejected`, `test_multi_column_unique_predicate_must_be_simple` |
| Disjoint/exhaustive declarations validate; absorb discriminator generates an explicit membership check | unit | parser + Rmap conformance tests | pass | `SubtypeCompletenessConformanceTests` |
| Generated Stage 03b models carry the new clauses and pass fidelity | unit | generator/data-model tests | pass | `test_generated_model_carries_the_unique_constraint`, `…role_and_subtype_constraints` |
| Postgres enforces multi-column uniqueness and discriminator membership | integration (Testcontainers) | `RmapEdgeBehaviorTest` | pass | P9 tenant/email partial uniqueness, P10 discriminator membership; legible-storage 38/38 |
| `--alter` replaces a changed CHECK expression under the same name | unit | `test_rmap.py` | pass | `test_alter_replaces_a_changed_check_expression` |
| Login migration and descriptor stay byte-identical | drift guard | `./clad rmap --check`, `verify_rmap_descriptor.py` | pass | both profile migrations and the descriptor report current |
| Full Python and PostgreSQL gates stay green | gate | `pytest`, `verify_artefacts.py`, postgres reactor | pass | pytest 655 passed; artefact pipeline intact; reactor 49/47/38/20/1 BUILD SUCCESS |

## Gates

### Design gate

Approved in-conversation (2026-11-17): implement items 1–3 (role-level
constraints/1:1 orientation, multi-column uniqueness, subtype
disjoint/exhaustive + explicit membership). Automatic predicate flipping and
richer SQL value types are deferred; the latter gets a pluggable type-registry
design rather than a guessed fixed set.

### Evidence gate

Approved (2026-11-17). Evidence: `pytest quality-gate/tests -q` → 655 passed;
`verify_artefacts.py` → artefact pipeline intact; `mvn -B -ntp verify -f
reference-impl/pom.xml -pl legible-storage,java-micronaut,java-plain -am
-Dclad.storage=postgres` → 49/47/38/20/1 BUILD SUCCESS; both login migrations
and the login descriptor report current; P9 (tenant/email partial uniqueness)
and P10 (discriminator membership) are green.

## Notes

- Non-goals this change: automatic 1:1 predicate re-orientation in the runtime;
  cross-table disjoint/exhaustive enforcement; general set-comparison
  constraints.
- **Type-registry follow-up (item 4).** Do not guess a fixed richer type set.
  The next change should add a small core (`Decimal`, `UUID`, `JSONB`, `Date`/
  `Time`, `Bytes`) plus a declarative extension point:
  `storage.type.<LogicalType>=<sql-type>` in `clad.properties` / per-concept
  `_config`, and a Java `ValueCodec` SPI for string↔SQL conversion. Unknown
  logical types must fail loudly unless registered. This keeps the core small
  and lets downstream applications declare the domain types they actually need.
- Rollback: revert the branch; the prior subset is reproduced by the previous
  parser/deriver/fixture set.
