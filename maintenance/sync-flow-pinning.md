# Maintenance change — `sync-flow-pinning`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** all profiles (the generator, the sync grammar, the stage contract, every feature's non-bootstrap sync specs, and the reference examples)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Every non-bootstrap sync names its **flow root** as its last `when` conjunct — `Web/request[routed]` with its route matcher. Nothing about outcomes, statuses, bodies or ordering changes: the same rules fire, on the same flows, in the same order.

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
  order-agnostic, but CLAD's engine evaluates a rule's `where` against its
  **primary (first) conjunct**: `WhereEvaluator` receives the primary invocation
  and completion, and `triggerField`/`triggerInput` read from those
  (`SyncEngine.processInvocation` → `evaluate(rule, primaryInv, primaryComp, …)`).
  The generated rules read the domain trigger with `triggerField`/`triggerInput`,
  so with the pin first those sources bind to the `Web/request` completion —
  which does not carry the domain fields — and the rule fires with blank
  arguments. The rule's own trigger therefore stays primary, and the pin follows
  it. (See §Review finding: the earlier "never re-evaluates" explanation was
  wrong; the engine re-checks every conjunct's completion.)
- **The pin is not a name component.** It appears in every non-bootstrap rule, so
  it carries no discriminating information — `CloseWhenVerifyVerified` keeps its
  name while its `when` gains a conjunct. This is the same reasoning that removed
  the pre-v0.6 `For<Scope>` (uniform ⇒ useless in a name) and the same reason the
  route *is* a component for bootstraps (not uniform ⇒ discriminating).
- **One rule, one flow.** A rule that must fire in two flows is two rules — a
  pin is a scope, not a filter (R11 one level down).
- **Mechanised.** `verify_sync_flow_pin.py` fails a non-bootstrap rule whose
  `when` does not name its flow root.

## Mechanism

`SyncEngine.processInvocation` hands a rule's **primary** (first) conjunct to
`WhereEvaluator` (reference-impl/legible-engine/src/main/java/dev/legible/engine/SyncEngine.java:270), and `triggerField`/`triggerInput`
resolve against it (reference-impl/legible-engine/src/main/java/dev/legible/engine/WhereEvaluator.java:98); a conjunct's own
completion/input is a separate source (`WhereEvaluator.java:107`). That is why
the pin is last: a pin first would make the `Web/request` completion the primary
and blank the domain fields.

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
| A rule without its flow root fails | unit | `verify_sync_flow_pin.py`; `test_sync_flow_pin.py::…test_unpinned_rule_fails` | pass | — |
| The pin must be the **last** conjunct | unit | `test_sync_flow_pin.py::…test_pin_before_the_domain_trigger_fails`, `…test_pin_in_the_middle_fails` | pass | — |
| More than one flow root fails | unit | `test_sync_flow_pin.py::…test_two_flow_roots_fail` | pass | — |
| The pinned route matches the chain's row 1 | unit | `test_sync_flow_pin.py::…test_pin_matching_the_chain_route_passes`, `…test_pin_drifted_from_the_chain_route_fails` | pass | — |
| Both repos' specs satisfy the narrowed checker | integration | `verify_sync_flow_pin.py` over each `features/` | pass | clad 6+1, experiment 25+5 |
| Pinned specs still match their Java rules | integration | `verify_sync_implementation_parity.py` per feature | pass | app suite green (experiment, 60) |
| UC-03's lend no longer fires in the return flow | acceptance | experiment `RespondWhenCloseNotOnLoanTest` + the joins | pass | green since the pin landed |
| Whole gate suite | unit | `pytest quality-gate/tests -q` | pass | 177 → 179 → 187 |

## Gates

### Design gate

Approved in-conversation: option (a), uniformly, per the sources' idiom — the pin
excluded from the name. The **position** was the one deviation forced during
implementation: approved as the sources' "request first", then corrected to
**last** when pin-first blanked the rules' arguments (see §Review finding). The
design intent — scope every rule to its own flow, leave the name alone — is
unchanged.

### Evidence gate

Cleared. The narrowed `verify_sync_flow_pin.py` (pin must be last; route must
match the chain's row 1) passes over both repos' features (clad 6 pinned + 1
bootstrap; experiment 25 pinned + 5 bootstraps), the gate suite is green at 187,
and the experiment's app suite (60) is green. The Item 4 review finding below is
the written confirmation the design gate asked for before merge.

## Notes

- Behaviour-preserving by construction: adding a conjunct can only *narrow* when a
  rule fires, and it narrows it to the flow it was written for.
- **The pin's position was found the hard way.** With the pin first, the
  experiment went to 9 errors and 5 failures — the rules fired, but with blank
  arguments (their `triggerField`/`triggerInput` bound to the request, not the
  domain trigger); with the pin last, to 3 failures. That difference is the
  primary-conjunct binding rule, recorded above so the next author does not
  repeat it.
- Validated on UC-04 before mass application: every non-bootstrap rule gained
  `requested: Web/request: [ route: "returns" ; method: "POST" ] => [ Routed ]`,
  every rule kept its name, and the two real joins kept theirs (`…WhenJoin…`).
- The blast radius is large — every non-bootstrap rule in both repos — which is
  why the design gate is separate from the implementation. Unlike the naming
  change, names do **not** change, so the churn is the specs' `when` blocks, the
  Java conjuncts, and the gate re-approvals.

## Review finding (Item 4)

The pin rule is the largest semantic change of the Model B experiment, so it was
re-reviewed before merge. Verdict: **the rule holds**, but its statement and its
mechanical enforcement had drifted from it. Corrected here and in the sources.

**The mechanism was misdescribed.** The rule originally said the engine
"dispatches a joined rule on its primary conjunct's completion, so a pin first
fires before its own trigger has completed and never re-evaluates." That is not
what the engine does: `buildTriggerIndex` files *every* conjunct and
`processInvocation` re-checks a rule on any conjunct's completion
(`SyncEngine.java:79-92, 266-269`), so a pin-first rule does fire — just wrongly.
`WhereEvaluator` is called with the primary conjunct as the trigger
(`SyncEngine.java:270-278`), and `triggerField`/`triggerInput` read its
completion/input (`WhereEvaluator.java:94-100`); with the pin first those sources
bind to the `Web/request` completion and the rule's arguments come out blank —
the experiment's 9 errors / 5 failures. Position still matters; the reason did
not.

**Four surfaces disagreed with the rule**, all now corrected:

1. `SYNCHRONIZATIONS.md` said "first conjunct" in its opening line and "last, not
   first" two paragraphs later; `generate_syncs.py` repeated "first". Both now
   say last, with the binding mechanism.
2. `verify_sync_flow_pin.py` accepted the pin anywhere and never compared its
   route to the chain — a pin-first or route-drifted spec passed. It now requires
   the pin to be the last conjunct, exactly one flow root, and the route to match
   a route the feature's Stage 01b chains root (with regression tests).
3. `templates/sync.md` documented joins, `absent`, `collect`, and route-scoped
   bootstraps but not the pin; the rule is now stated there.
4. This record's design gate said "pin first" and its test matrix still called the
   checker "pending"; both corrected.

**The four edge probes asked for:**

- *One rule, two flows.* Holds: the pin is a **scope**, not a filter, and a rule
  needed in two flows is two rules. One latent trap remains — `generate_syncs.py`
  `_edge_id` (line 326) ignores the pin, so two identical edges differing only by
  flow in a *single* feature would collapse silently. Not reachable today (one
  route per feature: every scenario in a feature shares row 1's route); flagged
  for a future multi-route feature.
- *A flow with more than one `Web/request`.* Not expressible under the current
  rule: `flow_route` is single-valued and derived from row 1 only
  (`generate_syncs.py:168-184`). The checker now rejects two roots; the grammar's
  one-flow-root-per-chain assumption should be stated if multi-request flows are
  ever wanted.
- *Shared trigger and shared target.* Correctness holds. The runtime emission
  guard is `(primary actionId, rule name)` (`SyncEngine.java:273`), so the two
  same-named `RespondWhenVerifyRefused` rules (routes `loans` / `returns`) never
  collide — only their traceability (`causedBySync`) is ambiguous, which is the
  separate naming item 2b.
- *Validate the pin against the chain.* Done: the checker now derives the
  feature's chain routes and rejects a spec whose pinned route is not among them.

No narrowing of the *behavioural* rule was needed; the narrowing is in its
enforcement and documentation.
