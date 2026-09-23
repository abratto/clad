# Maintenance change — `sync-name-grammar-v3`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** all profiles (gate + generator + docs + the UC-00 worked example)
- **Feature-contract impact:** `re-entered`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Sync names drop the scope and, by default, the concept tokens — `<TargetAction>When<TriggerAction><Completion>` — with a deterministic escalation that adds concept tokens back only on a genuine collision.

## Why

Sync names were too long to scan. Grammar v2 was
`<Target><Action>[For<Scope>]When<Trigger><Action><Completion>`, and two of
those components carry no information inside a sync pack:

- **`For<Scope>`** is derived from the feature folder slug
  (`UC-01-login` → `Login`), so every sync in a use case carries the *same*
  scope. It cannot disambiguate anything within the pack — it only repeats the
  folder name.
- **The trigger completion payload** (`RoutedRefName`, `EnrolledMemberid`) is
  body-visible; the completion *base* (`Routed`, `Enrolled`) is the
  discriminator.

Following the principle that **a sync is coordination, not a concept's
property** — it can involve several concepts — the concept tokens are also
redundant: the effect and its trigger read better as *action, when action
outcome*.

Observed on the library-lending experiment: 61–64 character stems for a
single-concept use case, e.g.
`MemberEnrolmentEnrolForEnrolMemberWhenWebRequestRoutedRefName` (61) vs the v3
form `EnrolWhenRequestRouted` (23).

## Grammar v3

```
<TargetAction>When<TriggerAction><Completion>
```

Joined (multi-`when`):

```
<TargetAction>WhenJoin<A1><Out1>And<A2><Out2>…
```

### Collision escalation

Two different concepts may share an action name (`Cataloguing.record` and
`Stocking.record`). The generator picks the **shortest level whose stem is
unique within the pack**, and the parity check accepts every level:

| Level | Form |
|---|---|
| 0 | `<TargetAction>When<TriggerAction><Completion>` |
| 1 | `<TargetConcept><TargetAction>When<TriggerAction><Completion>` |
| 2 | `<TargetAction>When<TriggerConcept><TriggerAction><Completion>` |
| 3 | `<TargetConcept><TargetAction>When<TriggerConcept><TriggerAction><Completion>` |

The `For<Scope>` component is removed entirely (it never disambiguated). The
`sync <Name>` header, filename stem, and Java class name stay identical.

## Mechanism

`artifact_parsers.sync_stem` builds the action-first, concept-free stem and the
`For<Route>` component; `generate_syncs.py` adds concept tokens back only on a
collision (`quality-gate/artifact_parsers.py#sync_stem`).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Only *names* change; the `when`/`then`/`where` rule bodies and outcomes are untouched |
| Action ordering and sync deduplication | `preserved` | Rule order in each sync file is unchanged |
| Flow-token lineage | `preserved` | Tokens are unchanged; only the `causedBySync` label moves |
| Storage/retention semantics | `preserved` | — |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine/runtime implementation | yes (one reference) | `reference-impl/legible-engine/.../Dsl.java` cites a sync name in its DSL doc |
| Gate scripts | yes | `artifact_parsers.sync_stem` (v3 + levels), `generate_syncs.py` (collision-chosen stem), `verify_implementation_parity.py` (accept levels) |
| Gate tests | yes | `test_generators.py`, `test_join_collect_grammar.py` |
| Methodology docs | yes | `SYNCHRONIZATIONS.md` §"Naming" |
| UC-00 artefacts | yes | 7 sync files renamed; 03a cards, pattern-d-summary, 04e derivation/`_IMPL`, 05 trace, README, usecase, chain tables re-cited |
| UC-00 implementation | yes | `LoginSyncs.java`; `java-micronaut-postgres` sync classes and rules renamed |
| UC-00 gates | yes | Gate 2 re-presented (03/03a outputs changed); Gate 3 re-presented if 04a–04c outputs changed |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Level-0 stem is action-first and concept-free | unit | `test_join_collect_grammar.py` | pass | `GrantWhenCheckOk`, `RespondWhenJoinListListedAndTagTagged` |
| Collision escalates to a longer unique stem | unit | `test_generators.py` fixtures | pass | ladder 0→3 + payload fallback |
| Generator names match the re-derived UC-00 pack | unit | `test_generators.py::test_generate_syncs_reproduces_canonical_names` | pass | 7 v3 stems |
| Parity accepts every level | unit | `test_parser_regressions.py`, `test_gap_checks.py` | pass | v3 fixture name accepted |
| UC-00 re-derivation is mechanically consistent | integration | `verify_artefacts.py`; `verify_stage_sequence --through 05` | pass (gates pending re-approval) | pipeline intact; gates stale by design |
| Reactor intact (all stocked profiles) | integration | `mvn -q test … -pl java-legible -am`; `-pl java-plain`; `mvn -q compile … -pl java-micronaut-postgres` | pass | exit 0 ×3 |
| Whole gate suite | unit | `pytest quality-gate/tests -q` | pass | 135 passed |

## Gates

### Design gate

Approved in-conversation: adopted the aggressive action-first form and chose
full re-derivation over grandfathering (`no legacy/current split`).

### Evidence gate

To be recorded from the executed test matrix and `verify_artefacts.py` before
commit.

## Notes

- Supersedes `maintenance/sync-dsl-legibility.md` (v2). v2 shipped with a full
  UC-00 re-entry and a Gate-2 re-approval; v3 does the same.
- Downstream CLAD projects inherit the generator and use v3 for new syncs.
