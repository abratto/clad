<!-- Maintenance-route planning record. -->
# Maintenance change — `sync-dsl-legibility`

> Platform change under `methodology/core/ITERATIVE_CHANGES.md`
> §"Platform maintenance changes" and R20. Readability DSL + naming-grammar
> v2 for syncs, not a feature-UC change: triggers, targets, outcomes,
> literals, route discrimination, and observable action order are
> **preserved** — only the declarative authoring surface and the sync
> *name grammar order* move.

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `active`
- **Affected profile(s):** `reference-impl/legible-engine` (DSL sugar), `reference-impl/java-legible` (migration, 27 rules), `reference-impl/java-micronaut-postgres` (migration, 7 rules + constants), `features/UC-00-login` (mechanical Stage 03 rename, R17 iterative re-entry), derived-repo migration tool
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** (A) fluent Java DSL (`Dsl.rule(...).when(...).matching(...).where(...).then(...).build()` + static `Clause`/`Source` factories and per-feature concept/action constants) so hand-written syncs read like the spec's `when → where → then` and remain directly debuggable Java (SPARQL-era property); (B) sync-name grammar v2, effect-first strict green-only: `When…Then…` → `<TargetConcept><TargetAction>[For<Scope>]When<TriggerConcept><TriggerAction><TriggerCompletion>` (paper-authors' own naming style, cf. conceptbox `NotifyWhenReachTen`); (3) `generate_syncs_java.py` — mechanical spec→code lowering emitting the DSL in both profile shapes with TODO markers only for judgement items. Deliberate non-adoption: `.sync.md`-as-runtime-data (Option 4) — the Legible goal is that the executed data is directly human-readable, debuggable *Java* (the SPARQL-era "no gap by readable code" property); the spec artefact/verification pairing remains the audit surface, so an interpreter would insert a hidden translation layer between spec and execution.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | same rules, same triggers/targets/args — only authoring shape and name order; FlowTrace/LoginFlow/Concurrency are the oracle |
| Action ordering and sync deduplication | `preserved` | same `SyncRule` record set emitted from sugar |
| Flow-token lineage | `preserved` (`causedBySync` values get the new names in migrated code — a renaming, not a remapping) |
| Storage/retention semantics | `preserved` | engine storage untouched |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `SYNCHRONIZATIONS.md` §"Naming" grammar v2 + example; `SYNC_ENGINE_EVOLUTION.md` legibility note; `templates/sync.md` naming-rule comment update; STAGES.md generator table |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | yes | new `Dsl.java` (fluent builder + `Clause`/`Source` factories); no record-type change |
| Profile tests | yes | 27 + 7 rules migrated; names/stems/classes renamed; `verify_test_naming` `<SyncName>Test` inherits the renamed stems |
| UC artefact chain | **yes — Stage 03 + post-gate stages mechanically renamed; Gate 2 re-approval required** |
| Quality-gate scripts | yes | `artifact_parsers` name grammar v2 (strict); `generate_syncs.py` stem derivation; `verify_implementation_parity.py` + `verify_sync_implementation_parity.py` mechanical lowering; `verify_sync_route_filters.py` evidence regex; new `generate_syncs_java.py` |

## Naming grammar v2 (canonical form)

```
<TargetConcept><TargetAction>[For<Scope>]When<TriggerConcept><TriggerAction><TriggerCompletion>
```

Examples (UC-00-login, before → after; token vocabulary unchanged, only order):

| v1 (condition-first) | v2 (effect-first, strict) |
|---|---|
| `WhenPasswordAuthCheckOkThenSessionGrantForLogin` | `SessionGrantForLoginWhenPasswordAuthCheckOk` |
| `WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin` | `WebRespondForLoginWhenPasswordAuthCheckBadPassword` |
| `WhenUserNamingLookupByUsernameRefusedThenWebRespondForLogin` | `WebRespondForLoginWhenUserNamingLookupByUsernameRefused` |
| `WhenWebRequestRoutedThenUserNamingLookupByUsernameForLogin` | `UserNamingLookupByUsernameForLoginWhenWebRequestRouted` |

`For<Scope>` stays glued to the effect side; token composition rules (PascalCase, completion tokenized from the outcome) unchanged — only order flips.

Historical carve-out: UC-00's frozen outputs pre-dating this record keep v1 stems until the R17 iterative rename lands for UC-00 (see Re-derivation order); `04d`/`04e` frozen examples are unchanged; `SYNCHRONIZATIONS.md` and the worked-example README document the v1→v2 mapping as a known historical deviation.

## Re-derivation order (R17 batch, one commit per gate)

1. `legible-engine` `Dsl` sugar (zerø behavior delta).
2. `java-legible` migration: DSL + constants + v2 names, 4 feature-sets / 27 rules.
3. `java-micronaut-postgres`: 7 rules + `LoginSyncRules` aggregator + constants.
4. `artifact_parsers` v2 grammar + `generate_syncs.py` stem derivation + parity/`test_naming`/route-filter verifiers.
5. New `generate_syncs_java.py` (both emitter shapes; TODO markers for Pattern D/non-literal args; property tests).
6. Stage-03 generator dry-run diff against migrated artefacts (UC-00) → rename + `_changes/` record + Gate-2 re-approval (human).
7. Docs + CHANGELOG (next release — numbering > 0.5.x per CLAD convention).
8. Evidence gate: full test matrix + canonical gate before commit.

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| DSL emits identical SyncRule data as today's builders (behaviour oracle) | feature | `mvn -f reference-impl/pom.xml test` post-migration | pass | full reactor green (engine 19, java-legible 40 incl. FlowTrace/Concurrency/Login/Tagging/Social/Token, storage 16, micronaut-postgres 16, bench 24) |
| v2 name grammar enforced mechanically | gate | `verify_implementation_parity` + `verify_sync_implementation_parity` on migrated trees | pass | 7/7 paired, strict_lowering v2 |
| Strict-only: legacy grammar rejected on new artefacts | gate | negative tests updated to grammar v2 (gap checks, parser regressions) | pass | quality-gate suite 85/85 OK |
| Generator (`generate_syncs_java.py`) output satisfies parity by construction | gate | dry-run of the 7 UC-00 rules (grammar-v2 names emitted) + generator table row wired | pass | dry-run listed 7 rule lines; stage wiring recorded in STAGES.md generator table |
| Canonical gate | gate | `test.command` (verify_artefacts + reactor) | pass | artefact pipeline intact |
| Docs links | gate | `verify_links.py` | pass | 304 links |

## Gates

### Design gate

Human approved in-conversation (fluent builder shape, concept/action constants, one bundled record, strict effect-first naming grammar, plus the explicit Option-4 non-adoption).

### Evidence gate

Pending human approval of the evidence summary presented in-conversation; the UC-00
rename iterative change (`sync-name-grammar-v2`) was already approved in its own
loop and committed (72ac629).

## Notes

- Naming v2 applies to *new and regenerated* artefact names; frozen Stage-03 outputs that pre-date this change keep v1 stems (documented deviation list in the worked example README).
- Derived repos (e.g. `foodsaver`) must run the mechanical rename tool over their `03_syncs/output` stems and Java rules before adopting this tree; strictness starts with this record's evidence gate.
