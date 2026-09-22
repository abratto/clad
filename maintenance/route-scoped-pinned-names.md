# Maintenance change — `route-scoped-pinned-names`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `active`
- **Affected profile(s):** all profiles (the generator, the stem grammar, `verify_implementation_parity`, the stage contract, and every feature's non-bootstrap sync names)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `pending`
- **Change summary:** Every **pinned** (non-bootstrap) sync's name now carries its flow route, exactly as a route-scoped bootstrap already does: `<TargetAction>For<Route>When<TriggerAction><Completion>` (and `…For<Route>WhenJoin…` for a joined rule). Nothing behavioural changes — the same rules fire on the same routes with the same outcomes — but two use cases can no longer register two differently-scoped pinned rules under one name.

## Why

Found by the library-lending experiment after flow pinning landed.

Pinning made UC-03's and UC-04's refusal rules **behaviourally** distinct — same
trigger (`MemberEnrolment.verify[Refused]`) and same target (`Web.respond[400]`),
different route — and both are registered. But grammar v3 named a pinned rule by
its trigger and target only (the pin is not a name component), so the two rules
share the name `RespondWhenVerifyRefused`. Nothing behavioural is wrong: the pin
routes each to its own flow, and `verify_sync_route_filters` checks the Java
matchers. The defect is legibility — `causedBySync` and the flow trace cannot say
which rule fired, in an architecture whose claim is *what you see is what it does*.

`route-scoped-sync-names` fixed this for **bootstraps**; this extends it to pinned
rules. The route is the same discriminator in both cases: the flow root a rule
belongs to. It is derivable — the generator already reads it from the chain's row 1
(`flow_route`) for every rule, and a pinned rule carries it in its pin.

A **collision-dependent** rule (add the route only when two packs collide) was
rejected: a single feature cannot see another feature's rules, so a pack-local
generator cannot decide it deterministically. The uniform rule is derivable.

## Rule

- A pinned rule's stem is `<TargetAction>For<Route>When<TriggerAction><Completion>`
  (a joined rule: `<TargetAction>For<Route>WhenJoin<…>`), where `<Route>` is the
  rule's flow root route.
- The **pin conjunct itself** (`requested: Web/request: …`) is still never a name
  component: it is in every non-bootstrap rule and names nothing. Its route is.
- `generate_syncs.py` passes `flow_route` to `sync_stem` for every rule (bootstraps
  already passed their route); `verify_implementation_parity.expected_sync_names`
  reads the route from the spec for pinned rules too.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No outcome, status, body, or literal changes |
| Action ordering and sync deduplication | `preserved` | Same rules, same triggers, same routes; only the names move |
| Flow-token lineage | `preserved` | The pin reads the same flow root; `causedBySync` becomes *more* precise |
| Storage/retention semantics | `preserved` | — |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine/runtime implementation | yes | `Dsl.java` doc-comment example only; no behaviour |
| Gate scripts | yes | `generate_syncs.py` (pass `flow_route`); `verify_implementation_parity.py` (route for pinned rules) |
| Gate tests | yes | `test_generators.py`, `test_join_collect_grammar.py`, `test_checker_shapes.py` |
| Templates | yes | naming examples |
| Methodology docs | yes | `SYNCHRONIZATIONS.md` naming, `WALKTHROUGH.md` |
| Corpus | no | — |
| Feature artefacts | yes | every non-bootstrap sync name in the worked example (`UC-00-login`) and the experiment (`UC-01`…`UC-04`) — Gate 2 re-approval per feature |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| A pinned rule's stem carries its route | unit | `test_generators.py::…test_the_pin_route_scopes_a_pinned_rules_name` | pass | — |
| A joined rule's stem carries its route | unit | `test_join_collect_grammar.py::…test_joined_chain_row_derives_joined_sync_stem` | pass | — |
| The parity checker derives the route-scoped name | unit | `test_checker_shapes.py::…test_pin_route_scopes_the_name_but_the_pin_conjunct_does_not` | pass | — |
| Whole gate suite | unit | `pytest quality-gate/tests -q` | pass | 202 |
| The worked example regenerates to the new names | integration | `generate_syncs.py --feature features/UC-00-login` | pass | — |
| The reactor builds | integration | `mvn -B -ntp test -f reference-impl/pom.xml` | pending | — |

## Gates

### Design gate

Approved in-conversation: the uniform rule (every pinned rule carries its route),
matching the bootstrap rule already shipped in `route-scoped-sync-names`. A
collision-dependent rule was rejected as non-derivable.

### Evidence gate

To be recorded before commit.

## Notes

- The blast radius is every non-bootstrap sync name in both repos, which is why the
  design gate is separate from the implementation. Behaviour is unchanged, so the
  only churn is the names, their Java rules, and the gate re-approvals.
