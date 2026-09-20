# Maintenance change — `sync-flow-pinning`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `active`
- **Affected profile(s):** all profiles (the generator, the sync grammar, the stage contract, every feature's non-bootstrap sync specs, and the reference examples)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Every non-bootstrap sync names its **flow root** as the first `when` conjunct — `Web/request[routed]` with its route matcher. Nothing about outcomes, statuses, bodies or ordering changes: the same rules fire, on the same flows, in the same order.

## Why

Found by UC-04-return-copy in the library-lending experiment, at Stage 04e-green,
with the engine's own error message as the evidence.

`MemberEnrolment.verify[verified]` triggers **both** UC-03's `lendWhenVerifyVerified`
and UC-04's `closeWhenVerifyVerified`, and nothing distinguishes them:

- in the **return** flow, UC-03's rule took the copy off the shelf — on a copy
  already out — and its `RespondWhenLendUnavailable` 409 won the response
  (`expected: <copy is not on loan to this member> but was: <copy is not on the
  shelf>`);
- in the **borrow** flow, UC-04's rule tried to close a loan that did not exist
  yet, and its `notOnLoan` 409 won.

R11 scopes the *bootstrap* by route, and the flow token scopes a match to *one*
flow — but within a flow, any rule whose `when` matches fires. Chain tables treat
row 1 as implicit thereafter, so Stage 03 lowered every later row to a
**single-conjunct** rule and the request was never named again.

### What the sources do

- **The paper** (§5.3, `RegistrationError`) names the request, matcher and all:
  `Web/request: [method: "register"] => [request: ?request]` **and** the failing
  action, explaining that "the link between the user registration failing and
  **the specific web request** … is essential, **as other web requests may be in
  process at the same time**".
- **§6.3** gives the semantics: "All action records matched in a synchronization's
  `when` clause must carry the same flow token." Flows scope matches; nothing
  *inside* a flow separates rules. In one app with one rule set that suffices;
  CLAD composes several use cases' packs, so two features can share a completion.
- **ConceptBox's guide** has a section titled *"Multiple When Clauses: Handling
  Request Flow"* and every non-bootstrap rule carries the request as a conjunct
  (`[Requesting.request, { path: "/LikertSurvey/addQuestion" }, { request }]`),
  for exactly this reason.

So the fix is the sources' own idiom, and CLAD already has the machinery (R15's
conjunct matcher plus joins). What is missing is that the lowering drops the pin.

## Rule

- **Every non-bootstrap rule pins its flow.** The flow root is the rule's **LAST**
  conjunct, carrying the route matcher:
  `when { … ; requested: Web/request: [ route: "returns" ] => [ Routed ] }`.
  **Last, not first** — and this is the one place the sources' shape does *not*
  transfer. The paper lists the request first and ConceptBox's `actions([...])` is
  order-agnostic, but CLAD's engine dispatches a joined rule on its **primary
  (first) conjunct's** completion: with the pin first the rule fires before its
  own trigger has completed and never re-evaluates, so it never fires at all. The
  rule's own trigger therefore stays primary, and the pin follows it.
- **The pin is not a name component.** It appears in every non-bootstrap rule, so
  it carries no discriminating information — `CloseWhenVerifyVerified` keeps its
  name while its `when` gains a conjunct. This is the same reasoning that removed
  the pre-v0.6 `For<Scope>` (uniform ⇒ useless in a name) and the same reason the
  route *is* a component for bootstraps (not uniform ⇒ discriminating).
- **One rule, one flow.** A rule that must fire in two flows is two rules — a
  pin is a scope, not a filter (R11 one level down).
- **Mechanised.** `verify_sync_flow_pin.py` fails a non-bootstrap rule whose
  `when` does not name its flow root.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No outcome, status, body, or literal changes |
| Action ordering and sync deduplication | `preserved` | The joined rule fires when all conjuncts completed in the flow — the same condition as before, now stated |
| Flow-token lineage | `preserved` | The pin reads the flow's root token; provenance is unchanged |
| Storage/retention semantics | `preserved` | — |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine/runtime implementation | no | The engine already supports multi-`when` rules and per-conjunct matchers (R15) |
| Gate scripts | yes | `generate_syncs.py` pins every non-bootstrap rule and keeps the pin out of the stem; new `verify_sync_flow_pin.py` |
| Gate tests | yes | the generator's pinned shape; the checker |
| Templates | yes | `templates/sync.md`; the 03 stage contract |
| Methodology docs | yes | `SYNCHRONIZATIONS.md` (the pin + the naming exception), `SYNC_PATTERNS.md` (the pin is a flow-root binding) |
| Corpus | no | — |
| Feature artefacts | yes | every feature's non-bootstrap sync specs gain the conjunct — clad `UC-00-login` and the login example's Java, experiment `UC-00`…`UC-04` — each needing Gate 2 re-approval |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Every non-bootstrap rule gains the pin | unit | `test_generators.py::…test_every_non_bootstrap_rule_pins_its_flow_root` | pass | — |
| The pin is absent from the stem | unit | `…test_the_pin_is_not_a_name_component` | pass | — |
| A rule without its flow root fails | unit | `verify_sync_flow_pin.py` | pending | checker not written yet |
| Pinned specs still match their Java rules | integration | `verify_sync_implementation_parity.py` per feature | pending | application to the features in progress |
| UC-03's lend no longer fires in the return flow | acceptance | experiment `RespondWhenCloseNotOnLoanTest` + the joins | pending | red today: `expected: <copy is not on loan to this member> but was: <copy is not on the shelf>` |
| Whole gate suite | unit | `pytest quality-gate/tests -q` | pass | 177 -> 179 |
| The pinned shape is what the generator emits | integration | dry run over UC-04's chain: pin with matcher, names unchanged | pass | see Notes |

## Gates

### Design gate

Approved in-conversation: option (a), uniformly, per the sources' idiom — with the
pin first and excluded from the name.

### Evidence gate

To be recorded before commit.

## Notes

- Behaviour-preserving by construction: adding a conjunct can only *narrow* when a
  rule fires, and it narrows it to the flow it was written for.
- **The pin's position was found the hard way.** With the pin first, the
  experiment went to 9 errors and 5 failures (rules that never fired); with it
  last, to 3 failures. That difference is the engine's dispatch rule, recorded
  above so the next author does not repeat it.
- Validated on UC-04 before mass application: every non-bootstrap rule gained
  `requested: Web/request: [ route: "returns" ; method: "POST" ] => [ Routed ]`,
  every rule kept its name, and the two real joins kept theirs (`…WhenJoin…`).
- The blast radius is large — every non-bootstrap rule in both repos — which is
  why the design gate is separate from the implementation. Unlike the naming
  change, names do **not** change, so the churn is the specs' `when` blocks, the
  Java conjuncts, and the gate re-approvals.
