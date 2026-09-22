# Maintenance change — `route-scoped-sync-names`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** all profiles (the generator, the stem grammar, the stage contract, and every feature's bootstrap sync name)
- **Feature-contract impact:** `preserved`
- **Design gate:** `pending`
- **Evidence gate:** `pending`
- **Change summary:** A route-scoped bootstrap sync's name carries its route: `<TargetAction>For<Route>When<TriggerAction><Completion>`. Nothing behavioural changes — the same rules fire on the same routes with the same outcomes — but two use cases can no longer register two differently-scoped rules under one name.

## Why

Found by UC-04-return-copy in the library-lending experiment, at the moment
Stage 04e would have registered the rules.

Two of UC-04's eight sync names were **already registered by UC-03**:

| Name | UC-03 | UC-04 |
|---|---|---|
| `VerifyWhenRequestRouted` | `Web.request[routed]` on route `loans` | `Web.request[routed]` on route `returns` |
| `RespondWhenVerifyRefused` | `MemberEnrolment.verify[Refused]` | the same rule |

Grammar v3 names a sync action-first and concept-free, and the route lives in the
`matching(...)` matcher rather than the name, so two features bootstrapping the
*same target action* on *different routes* produce *identical* names. UC-01 and
UC-02 escaped by luck: their bootstraps target different actions (`enrol`,
`record`). UC-03 and UC-04 both check a `memberId` and both answer a refusal.

**Why it matters.** Nothing behavioural is wrong: the routes differ, R11 is
satisfied, and `verify_sync_route_filters` checks the Java matchers. The defect is
legibility — `LibrarySyncs` would register two rules with one name, so
`causedBySync` and the flow trace can no longer say which rule fired, in an
architecture whose claim is *what you see is what it does*.

A second, smaller gap surfaced with it: the generator could only read a route
from a chain row written `route: "…"`, while chain tables write
`Web/request[POST /loans]` — so the derived bootstrap had **no route matcher at
all**, and the spec understated the rule (the Java carried it by hand). Both are
fixed together, because the name's route comes from the same parse.

## Rule

- **`For<Route>`.** The stem gains the component **exactly when the rule has a
  route matcher**, so the name is derivable from the rule rather than chosen:
  `EnrolForMembersWhenRequestRouted`, `RecordForTitlesWhenRequestRouted`,
  `VerifyForLoansWhenRequestRouted`, `VerifyForReturnsWhenRequestRouted`.
- **This is not a revival of the pre-v0.6 `For<Scope>`.** That component held the
  *feature slug*, so every sync in a use case carried the same value and it could
  never disambiguate anything — removing it was right. The route is a real
  discriminator within one app, which the slug never was.
- **The chain's flow root is parsed for the route.** `Web/request[POST /loans]`
  yields method `POST` and route `loans`, so the generated bootstrap carries the
  matcher in its spec and not only in the implementation.
- Route-scoped means *any* `Web/request` bootstrap; the rule is uniform rather
  than "only when two would collide", because a rule with a collision-dependent
  exception is not derivable.
- `RespondWhenVerifyRefused` needs no scope: it is one rule with one trigger and
  no route, and the two features derive the same rule. A shared implementation
  registers it once.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No outcome, status or body changes; names only |
| Action ordering and sync deduplication | `preserved` | Same rules, same routes, same order |
| Flow-token lineage | `preserved` | `causedBySync` merely becomes unambiguous |
| Storage/retention semantics | `preserved` | — |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine/runtime implementation | no | — |
| Gate scripts | yes | `artifact_parsers.sync_stem` gains the `route` component; `generate_syncs.py` parses the chain's `METHOD /path` root |
| Gate tests | yes | the stem's route form; the generator's route derivation |
| Templates | yes | `templates/sync.md` names the rule |
| Methodology docs | yes | `SYNCHRONIZATIONS.md` naming section |
| Corpus | no | — |
| Feature artefacts | yes | five bootstrap syncs renamed with their route matcher added — clad `UC-00-login`, experiment `UC-00`…`UC-04` — each needing Gate 2 re-approval (and `UC-00` also Gate 1, because the chain's notes name the sync) |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| The stem carries the route when given | unit | `test_join_collect_grammar.py` / `test_machine_contract.py` stem cases | pending | — |
| The generator derives the route from `METHOD /path` | unit | `generate_syncs.py` on a chain whose root is `Web/request[POST /x]` | pending | — |
| Renamed specs still match their Java rules | integration | `verify_sync_implementation_parity.py` per feature | pass | UC-00/01/02/03 pass; UC-04 pending 04e |
| No duplicate names in one app | unit | `features/_system/shared-triggers.md` shows one name per trigger-route | pending | — |
| Whole gate suite | unit | `pytest quality-gate/tests -q` | pending | — |

## Gates

### Design gate

Approved in-conversation: option (a), uniformly across every route-scoped
bootstrap, with the `For<Route>` refinement (route, not feature slug).

### Evidence gate

To be recorded before commit.

## Notes

- The rename is mechanical and behaviour-preserving; the gate re-approvals exist
  because a gated stage's output changed.
- The shared-trigger view had gone stale since grammar v3, which is why this
  surfaced only at 04e rather than at Stage 03a. Wiring it so it cannot go stale
  is part of this change.
