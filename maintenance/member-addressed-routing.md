# Maintenance change — `member-addressed-routing`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `active` (`draft` until design approval, `active` while
  implementing, `closed` after evidence approval)
- **Affected profile(s):** `reference-impl/legible-engine` (the `Region` SPI),
  `reference-impl/legible-storage` (`RmapPostgresFactStore`), the relational
  doctrine docs
- **Feature-contract impact:** `preserved` (the composite-subject precedent:
  new **default** methods only — existing callers and backends unchanged;
  the in-memory and generic-fact backends ignore the member, which is their
  correct semantics, since conceptually a concept region is one region)
- **Design gate:** `approved` (human, in-conversation: "do it" — the deferred
  item from `relational-gaps-closure`: give partitioned supertypes a runtime
  write path via member-addressed operations)
- **Evidence gate:** `approved`
- **Change summary:** Add member-qualified operations to the `Region` SPI
  (`read/write/remove/clear(member, subject, …)`, default methods that ignore
  the member), and route them in `RmapPostgresFactStore` to the member's own
  table — closing the partition runtime gap: a partitioned supertype's region
  is now creatable, a member write lands in the member's table (the mandatory
  flattened predicate becomes satisfiable per member), and plain operations
  on a multi-owner predicate throw at operation time naming the members
  (replacing the whole-region creation refusal).

## Mechanism

- **SPI (legible-engine).** `Region` gains member-qualified default
  overloads that delegate to the plain forms — the composite-subject
  precedent exactly: backends that do not model members (the in-memory
  store, the generic fact relation) ignore the member, which is their
  correct semantics — a concept region is conceptually one region; members
  are a relational-realization dimension (partition/separate subtypes).
- **Member table resolution (legible-storage).** A partition/separate
  member's table reports the **supertype** as its `objectType`
  (`RmapDeriver.realizeTable`), so `tableFor(objectType)` cannot distinguish
  members. Resolution is by the deriver's own naming convention:
  `snake(concept) + "__" + snakeName(member)` (non-single models), exposed
  as `RmapDeriver.memberTableName` + `RmapModel.tableForMember`. An absorbed
  member has no table (its predicates live on the supertype's table with
  unique ownership) — a member write for one throws with that explanation.
- **Routing.** `RmapRegion` indexes multi-owner data predicates at
  construction (the old creation-time refusal becomes data): plain
  operations on a multi-owner predicate throw at **operation time** naming
  the member form; member-qualified operations resolve the member's table
  and route read/write/remove/clear there (unqualified table drafts already
  buffer per table, so `TransactionalRegion` flush works unchanged — a
  member write's row lands wholly in the member's table, which is what
  makes a **mandatory flattened predicate satisfiable**: the member's own
  row carries it).
- **Doctrine.** `RELATIONAL_LOWERING.md`'s partition row flips from "not
  runtime-routable / store refuses the region" to "runtime-routable via
  member-qualified operations; plain operations on shared predicates throw
  naming the members"; `RELATIONAL_RMAP.md`'s guardrail and
  `STORAGE_MAPPING.md`'s sentences updated; the `Region` javadoc documents
  the member semantics; the P3 probe (`RmapEdgeBehaviorTest`) pins the new
  behavior (the intended upgrade path it was written for).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Default methods only; no existing caller changes; shipped suites green. |
| Action ordering and sync deduplication | `preserved` | Engine `execute` wrapper untouched. |
| Flow-token lineage | `preserved` | Untouched. |
| Storage/retention semantics | `preserved` (extended) | Partition regions: creation now succeeds; member writes land in the member's table; plain writes on shared predicates fail loudly at the operation. Non-partition behavior byte-identical. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `Region` javadoc, `RELATIONAL_LOWERING.md`, `RELATIONAL_RMAP.md`, `STORAGE_MAPPING.md`. |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | yes | `legible-engine/Region.java` (member overloads); `legible-storage`: `RmapDeriver.memberTableName`, `RmapModel.tableForMember`, `RmapPostgresFactStore` (op-time ambiguity + member routing). |
| Profile tests | yes | `RmapMemberRoutingTest` (Testcontainers) + `RmapEdgeBehaviorTest` P3 rewritten + engine-level default-semantics test. |
| UC artefact chain | no | No shipped concept uses partition. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| In-memory/generic backends ignore the member (default semantics) | unit | `RmapMemberRoutingTest#inMemoryBackendIgnoresTheMember` | pass | member-qualified write/read ≡ plain on `InMemoryFactStore` (the Region defaults) |
| Partition region creatable; member write/read round-trip; mandatory flattened predicate satisfiable | integration (Testcontainers) | `RmapEdgeBehaviorTest#partitionRoutingIsMemberAddressed` (P3 rewritten) | pass | region creatable; plain write throws naming members; buffered member flush writes the client's own row (mandatory `party_name` satisfied); supplier wholly in its own table; member retract stays in-member |
| Plain operation on a shared predicate throws naming the members | integration | `RmapEdgeBehaviorTest#partitionRoutingIsMemberAddressed` | pass | `IllegalArgumentException` names `partyName`, both members, and the member-qualified form |
| Separate-mapping member write routes to the subtype table | integration | `RmapMemberRoutingTest#separateMemberWriteRoutesToTheSubtypeTable` | pass | `Patient` member write lands in `patient_registry__patient`; naming the supertype routes to its own table |
| Absorbed/unknown member throws with the explanation; a member not owning the predicate fails | integration | `RmapMemberRoutingTest#memberErrorsAreHonest` | pass | unknown member + absorbed member + not-owned predicate all fail loudly with the reason |
| Non-partition behavior unchanged | reactor | existing suites | pass | postgres reactor 41/47/69/21/2 BUILD SUCCESS (69 = 66 + 3 member tests); `RmapMigrationTest` drift guard byte-identical (login untouched by partition) |

## Gates

### Design gate

Approved in-conversation (2026-10-06). Decisions: default methods on
`Region` (no new capability interface — the member is ignored by
member-agnostic backends by design); op-time ambiguity instead of
creation-time refusal (the refusal threw away the whole region including
member-addressable routing); resolution by the deriver's naming convention
(objectType cannot distinguish members — they report the supertype).

### Evidence gate

Approved — matrix above: postgres reactor 41/47/69/21/2 BUILD SUCCESS
(RmapMemberRoutingTest 3 cases + P3 rewritten green), login drift guard
byte-identical, in-memory default semantics pinned, pytest 377 passed,
artefact gate intact. Status stays `active` through the code commit (the
pre-commit hook requires one active evidenced record for engine-scoped
files) and flips to `closed` in the follow-up documentation-only commit.

## Notes

- Commit sequencing (the pre-commit hook requires exactly one **active**
  record with an approved evidence gate when engine-scoped files are
  staged): the code commits with this record `active` + evidence approved;
  the status flips to `closed` in a documentation-only follow-up commit.
- Composite subjects + members: a partition member is keyed on the
  supertype's single identity, so member addressing never combines with
  composite subjects; documented, not modelled.
- `subjects(predicate, value)` remains member-unqualified (documented) —
  the inverse read over a partitioned predicate is ambiguous by the same
  argument and gets a member form only if a consumer appears.
- Rollback: remove the member overloads and the routing; the creation-time
  guard returns.
