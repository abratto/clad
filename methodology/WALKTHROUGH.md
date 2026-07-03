# WALKTHROUGH.md — UC-00-login, turn by turn

This is a **worked example of a CLAD session** — the same UC-00-login
feature that the rest of the repo uses, replayed as the sequence of
human↔agent turns it would take to produce. Each turn shows:

- the `CONTEXT.md` the agent loaded that turn,
- the specific `Inputs` from that CONTEXT it actually opened,
- the `output/` it wrote,
- the gate question it asked, and
- the **agent stance** appropriate to the turn.

It is meant to be read in two ways:

1. **Humans onboarding to CLAD** — read top-to-bottom; you will see
   the whole 00→05 loop in one sitting using a single small example.
2. **Agents in mid-flight** — when you are about to start Stage NN,
   skim the matching turn here to see what the *shape* of a clean
   turn for that stage looks like. The pattern repeats: load
   `CONTEXT.md`, open only the named `Inputs`, write only into
   `output/`, ask the gate question, stop.

Throughout this walkthrough, the **gate question** is the canonical
one from
[`../templates/feature-skeleton/stages/*/CONTEXT.md`](../templates/feature-skeleton/):

> **Do you agree with this step? Any corrections before I continue?**

If a turn modifies the canonical phrasing — typically Stage 00, which
is multi-turn before any artefact is written — that is called out
inline.

---

## Turn 0 — the human's brief

> **Single-goal edge-case note.** UC-00-login is a deliberately minimal
> example: one actor, one in-scope goal. In a real multi-goal system,
> Stage 00 runs once at system scope inside
> `features/_system/stages/00_actor-goal/`, and each in-scope goal from
> `goals.md` then becomes its own `features/UC-XX-<slug>/` folder at
> Stage 01. Here, because there is only one goal, the Stage 00 output
> (actors + goal) and the single UC folder happen to coincide — so
> `UC-00-login/stages/00_actor-goal/` doubles as both. Do **not** use
> this co-location as a template for new work. See
> [`../methodology/implementation/STAGES.md`](implementation/STAGES.md)
> §"Scope: system-level vs per-UC" for the correct multi-UC structure.

> **Human:** *"I want to add login. Username and password. On success
> they get a session token. On failure, the error message must not
> reveal whether the username exists. After several failed attempts
> the account locks for a while."*

This is the only thing the agent has. The brief is *not* a use case —
it has no scenarios, no actors named except by implication, no
postconditions. The agent's job at Stage 00 is to turn it into one.

> **Agent stance for Turn 0:** do **not** start writing artefacts.
> Stage 00 is multi-turn collaborative; the brief is the input to a
> conversation, not to a file write.

---

## Turn 1 — Stage 00 (Actor / Goal), proposal + clarifying questions

**CONTEXT loaded:** [`features/UC-00-login/stages/00_actor-goal/CONTEXT.md`](../features/UC-00-login/stages/00_actor-goal/CONTEXT.md)

**Inputs opened (per that CONTEXT):**

- the human's brief (Turn 0).
- [`templates/actors.md`](../templates/actors.md) — output template.
- [`templates/goals.md`](../templates/goals.md) — output template.
- [`methodology/implementation/STAGES.md`](implementation/STAGES.md) §"Stage 00" — collaboration semantics.

**Agent action:** propose an actor list and a goal list, then ask **at
most 5 clarifying questions** before writing anything:

> **Agent (proposal):** I read one in-scope actor `EndUser`. I read
> three in-scope goals: `Sign In`, `See Safe Failure Message`,
> `Understand Lockout`. Their rationales are obtaining a session,
> retrying without learning whether the username exists, and
> understanding why retrying does not work. I read these out-of-scope:
> registration, password reset, MFA, SSO, email-as-identity, logout.
>
> Before I write `actors.md`/`goals.md`, four questions:
>
> 1. Is `EndUser` the only actor — i.e. no admin / no operator?
> 2. Is "lockout" a *goal* (visible to the user) or just a *mechanism*
>    that supports the no-enumeration goal?
> 3. Is logout in scope? You didn't mention it.
> 4. Is the username opaque (no email semantics)?

**Output written:** *(none yet — Stage 00 is multi-turn)*.

**Gate phrasing for this turn:** the canonical question doesn't fire
yet. Stage 00 instead asks its clarifying questions and waits for the
human's answers.

---

## Turn 2 — human answers, agent writes Stage 00 artefacts

> **Human:** *"1) yes; 2) lockout is a visible goal — they need to
> understand why retries fail; 3) out of scope; 4) opaque."*

**Agent action:** **only now** write the artefacts.

**Outputs written:**

- [`features/UC-00-login/stages/00_actor-goal/output/actors.md`](../features/UC-00-login/stages/00_actor-goal/output/actors.md) — one row, `EndUser`.
- [`features/UC-00-login/stages/00_actor-goal/output/goals.md`](../features/UC-00-login/stages/00_actor-goal/output/goals.md) — three in-scope goals; six out-of-scope items.

**Gate question (canonical):** *"Do you agree with this step? Any
corrections before I continue?"*

> **Why this matters downstream:** every later stage cites these.
> `actors.md` will appear verbatim as the use case's *Actors*
> section. Each in-scope `goals.md` row contributes a stable goal name
> plus rationale that becomes ≥1 named scenario in Stage 01.

---

## Turn 3 — Stage 01 (Use case), Fully Dressed

**CONTEXT loaded:** [`features/UC-00-login/stages/01_usecase/CONTEXT.md`](../features/UC-00-login/stages/01_usecase/CONTEXT.md)

**Inputs opened:**

- `../00_actor-goal/output/actors.md` — for the *Actors* section.
- `../00_actor-goal/output/goals.md` — every in-scope goal becomes ≥1 scenario.
- [`methodology/core/CLAD.md`](core/CLAD.md) — methodology.
- [`templates/usecase.md`](../templates/usecase.md) — Brief / Casual / **Fully Dressed** template.

**Agent action:** check the **Fully Dressed** completeness box; one
operational principle paragraph; one named scenario per in-scope
goal (`successful-login`, `wrong-password`, `unknown-user`, `lockout`);
each scenario gets *Pre-conditions*, *Main flow* (numbered), *Expected
outcomes*, **and both** *Postconditions—Success* and
*Postconditions—Failure* (the Failure block may say *"no state is
modified"* but must be present); explicit *Out of scope* + *Relationship
to other use cases* (Registration, Logout, Password reset).

**Output written:** [`features/UC-00-login/stages/01_usecase/output/usecase.md`](../features/UC-00-login/stages/01_usecase/output/usecase.md).

**Gate question (canonical).**

> **Why this matters downstream:** the canonical action names
> (`User.lookupByUsername`, `PasswordAuth.check`, `Session.grant`)
> first appear in this file. Stage 02b will lock them in; Stage 03
> must not invent different names. Every Stage 04c flow test will
> assert one scenario from this file.

---

## Turn 4 — Stage 02a (Responsibility map)

**CONTEXT loaded:** [`features/UC-00-login/stages/02a_responsibility-map/CONTEXT.md`](../features/UC-00-login/stages/02a_responsibility-map/CONTEXT.md)

**Inputs opened:**

- `../01_usecase/output/usecase.md` — scenarios to cover.
- `../00_actor-goal/output/actors.md` — for the cross-stage check.
- [`methodology/architecture/CONCEPTS.md`](architecture/CONCEPTS.md) — what counts as a concept.
- [`methodology/implementation/RULES.md`](implementation/RULES.md) — R1.
- [`templates/responsibility-map.md`](../templates/responsibility-map.md).

**Agent action:** identify four concepts — `User`, `PasswordAuth`,
`Session`, `Web` — each with a *one-line* state and a comma-separated
action list, **no signatures, no outcomes**. Add a *Coverage check*
section pairing each scenario to the concepts it touches. Add an *Out
of scope* section recording what was deliberately not made into a
concept (e.g. `LoginAttemptHistory`).

**Output written:** [`features/UC-00-login/stages/02a_responsibility-map/output/responsibility-map.md`](../features/UC-00-login/stages/02a_responsibility-map/output/responsibility-map.md).

**Gate question (canonical).**

> **Agent stance:** if you find yourself wanting to write
> `lookupByUsername(username) -> Found(userId) | NotFound`, you are
> doing Stage 02 work in Stage 02a. Names only.

---

## Turn 5 — Stage 02b (Chain tables)

**CONTEXT loaded:** [`features/UC-00-login/stages/02b_chain-table/CONTEXT.md`](../features/UC-00-login/stages/02b_chain-table/CONTEXT.md)

**Inputs opened:**

- `../01_usecase/output/usecase.md` — scenarios.
- `../02a_responsibility-map/output/responsibility-map.md` — available concepts and actions.
- [`methodology/architecture/SYNCHRONIZATIONS.md`](architecture/SYNCHRONIZATIONS.md) — so the chain can be lifted into syncs later.
- [`templates/chain-table.md`](../templates/chain-table.md).

**Agent action:** one file per scenario, each with a numbered table
of `<Concept>.<action> -> <outcome>` rows + (optional) Mermaid
diagram. First row is always `Web.handle`; last row is always
`Web.respond` (R4). The *Why this step* column justifies each row.

**Outputs written:**

- [`successful-login-chain.md`](../features/UC-00-login/stages/02b_chain-table/output/successful-login-chain.md)
- [`wrong-password-chain.md`](../features/UC-00-login/stages/02b_chain-table/output/wrong-password-chain.md)
- [`unknown-user-chain.md`](../features/UC-00-login/stages/02b_chain-table/output/unknown-user-chain.md)
- [`lockout-chain.md`](../features/UC-00-login/stages/02b_chain-table/output/lockout-chain.md)

**Gate question (canonical).**

> **Why this matters downstream — the canonical-name rule:** if a
> Stage 03 sync spec later disagrees with a chain table on an action
> name, **the chain table wins**. PR #6 reconciled `Session.open` →
> `Session.grant` and `PasswordAuth.verify` → `PasswordAuth.check`
> precisely on this rule.

---

## Turn 6 — Stage 02 (Concept specs)

**CONTEXT loaded:** [`features/UC-00-login/stages/02_concepts/CONTEXT.md`](../features/UC-00-login/stages/02_concepts/CONTEXT.md)

**Inputs opened:**

- `../01_usecase/output/usecase.md`.
- `../02a_responsibility-map/output/responsibility-map.md` — agreed concept set.
- `../02b_chain-table/output/` — agreed action choreography (action names, outcomes).
- `../00_actor-goal/output/actors.md` — for cross-stage check.
- [`methodology/architecture/CONCEPTS.md`](architecture/CONCEPTS.md), [`RULES.md`](implementation/RULES.md), [`templates/concept.md`](../templates/concept.md).

**Agent action:** one `<Name>.concept.md` per row of the
responsibility map. Each concept's `state`, `actions` (signatures +
outcomes — must match the chain tables), `flow_token` shape, and
operational principle. **R1 enforced**: the `Session` spec does not
mention `User`'s state; it works with opaque `UserId`.

`Web` does **not** get a `.concept.md` — see
[`methodology/architecture/WEB_CONCEPT.md`](architecture/WEB_CONCEPT.md).

**Outputs written:**

- [`User.concept.md`](../features/UC-00-login/stages/02_concepts/output/User.concept.md)
- [`PasswordAuth.concept.md`](../features/UC-00-login/stages/02_concepts/output/PasswordAuth.concept.md)
- [`Session.concept.md`](../features/UC-00-login/stages/02_concepts/output/Session.concept.md)

**Gate question (canonical).**

> **Agent stance:** if you find yourself writing `import com…User`
> inside `Session.concept.md`, stop — that coupling belongs in a sync
> (Stage 03), not in a concept spec.

---

## Turn 7 — Stage 03 (Syncs)

**CONTEXT loaded:** [`features/UC-00-login/stages/03_syncs/CONTEXT.md`](../features/UC-00-login/stages/03_syncs/CONTEXT.md)

**Inputs opened:**

- `../01_usecase/output/usecase.md` — scenarios to satisfy.
- `../02_concepts/output/` — concepts to coordinate.
- `../02b_chain-table/output/` — the action chain each sync formalises.
- [`methodology/architecture/SYNCHRONIZATIONS.md`](architecture/SYNCHRONIZATIONS.md), [`SYNC_PATTERNS.md`](architecture/SYNC_PATTERNS.md), [`RULES.md`](implementation/RULES.md), [`templates/sync.md`](../templates/sync.md).

**Agent action:** one `*.sync.md` per cross-concept link in the
chains. Each sync is `when … where … then` — declarative, no
branching, no state, no I/O. Every `where` clause labels its pattern
(`A:` / `B:` / `C:` / `D:`).

For UC-00 the agent writes:

- [`WhenPasswordAuthCheckOkThenSessionGrantForLogin.sync.md`](../features/UC-00-login/stages/03_syncs/output/WhenPasswordAuthCheckOkThenSessionGrantForLogin.sync.md) — `when PasswordAuth.check(userId, password) -> Ok` then `Session.grant(userId)` then `Web.respond(200, { sessionToken })`. The `where: B: sessionId = result_of(Session.grant).sessionId` is **Pattern B** (flow-sibling); see [`SYNC_PATTERNS.md`](architecture/SYNC_PATTERNS.md).
- [`WhenPasswordAuthCheckLockedThenWebRespondForLogin.sync.md`](../features/UC-00-login/stages/03_syncs/output/WhenPasswordAuthCheckLockedThenWebRespondForLogin.sync.md) — lockout response path.

The unhappy paths (`wrong-password`, `unknown-user`, `lockout`) are also
syncs. Stage 03 remains the single declarative coordination surface for
both success and failure responses.

**Gate question (canonical).**

> **Agent stance:** if a sync needs `if`, the `if` belongs in the
> upstream concept's outcome enum, not in the sync. Push branching
> *down* into the action that decides; the sync only routes outcomes.

---

## Turn 8 — Stage 03a (Dependency review)

**CONTEXT loaded:** [`features/UC-00-login/stages/03a_dependency-review/CONTEXT.md`](../features/UC-00-login/stages/03a_dependency-review/CONTEXT.md)

**Inputs opened:**

- `../03_syncs/output/` — every `then` invocation, every `where` clause.
- `../02b_chain-table/output/` — the flows.
- `../02a_responsibility-map/output/responsibility-map.md` — concept set.
- `../02_concepts/output/` — action and field names to cite.
- [`methodology/architecture/SYNC_PATTERNS.md`](architecture/SYNC_PATTERNS.md).
- [`templates/dependency-review-card.md`](../templates/dependency-review-card.md), [`templates/pattern-d-summary.md`](../templates/pattern-d-summary.md).

**Agent action:** one card per concept (Section 1 = inbound calls
with Pattern; Section 2 = inbound Pattern D reads — for UC-00 this is
**none** for every concept), then one consolidated
`pattern-d-summary.md`.

This is the stage that *first surfaced* the action-name discrepancy
between Round 4 sync specs and Round 4 chain tables — captured in the
old "Inconsistencies" rows of `Session-card.md` and `pattern-d-summary.md`,
now resolved (per PR #6 — the chain tables won).

**Outputs written:**

- [`User-card.md`](../features/UC-00-login/stages/03a_dependency-review/output/User-card.md)
- [`PasswordAuth-card.md`](../features/UC-00-login/stages/03a_dependency-review/output/PasswordAuth-card.md)
- [`Session-card.md`](../features/UC-00-login/stages/03a_dependency-review/output/Session-card.md)
- [`Web-card.md`](../features/UC-00-login/stages/03a_dependency-review/output/Web-card.md)
- [`pattern-d-summary.md`](../features/UC-00-login/stages/03a_dependency-review/output/pattern-d-summary.md)

**Gate question (canonical).**

> **Agent stance:** *no new design here.* If a card needs an action
> that doesn't yet exist in any `.concept.md`, you are mid-violation
> — return to Stage 02 (or 02b first).

---

## Turn 9 — Stage 04 (Implement, sub-stages 04a → 04e)

**Router CONTEXT loaded:** [`features/UC-00-login/stages/04_implement/CONTEXT.md`](../features/UC-00-login/stages/04_implement/CONTEXT.md)

The router has **no artefact of its own** — it gates after each
sub-stage. The five sub-stages run in order; each one is its own turn
with its own `CONTEXT.md`. For UC-00 in this round:

- **03b (Data model):** the conceptual state model is written before implementation. CONTEXT loaded: [`../features/UC-00-login/stages/03b_data-model/CONTEXT.md`](../features/UC-00-login/stages/03b_data-model/CONTEXT.md).
- **04a (Storage mapping):** the in-memory profile triggers `_NOT_APPLICABLE.md`. CONTEXT loaded: [`04a_storage-mapping/CONTEXT.md`](../features/UC-00-login/stages/04_implement/04a_storage-mapping/CONTEXT.md).
- **04b (SPEC):** mechanically extract action signatures and outcome enums per concept. CONTEXT loaded: [`04b_spec/CONTEXT.md`](../features/UC-00-login/stages/04_implement/04b_spec/CONTEXT.md).
- **04c (Flow tests, outer red):** a Gherkin `.feature` file, step-definition skeleton, Cucumber runner, and `@Disabled` stub flow tests per use case. CONTEXT loaded: [`04c_flow-tests/CONTEXT.md`](../features/UC-00-login/stages/04_implement/04c_flow-tests/CONTEXT.md).
- **04d (Concept TDD router):** structural handoff point for concept red/green. Open [`04d_concept-tdd/CONTEXT.md`](../features/UC-00-login/stages/04_implement/04d_concept-tdd/CONTEXT.md), then run [`04d_red-tests/CONTEXT.md`](../features/UC-00-login/stages/04_implement/04d_concept-tdd/04d_red-tests/CONTEXT.md) to derive red concept tests (automated gate: `verify_concept_test_derivation.py`), followed by [`04d_green-impl/CONTEXT.md`](../features/UC-00-login/stages/04_implement/04d_concept-tdd/04d_green-impl/CONTEXT.md) to implement them.
- **04e (Sync TDD router):** structural handoff point for sync red/green. Open [`04e_sync-tdd/CONTEXT.md`](../features/UC-00-login/stages/04_implement/04e_sync-tdd/CONTEXT.md), then run [`04e_red-tests/CONTEXT.md`](../features/UC-00-login/stages/04_implement/04e_sync-tdd/04e_red-tests/CONTEXT.md) to derive red sync tests (automated gate: `verify_sync_matrix.py`), followed by [`04e_green-impl/CONTEXT.md`](../features/UC-00-login/stages/04_implement/04e_sync-tdd/04e_green-impl/CONTEXT.md) to implement them and turn the `04c` flow tests green.

**Human gates across the loop:** Gate 1 (02b — Requirements), Gate 2 (03b — Architecture), **Gate 3 (04c — Executable specification)**. No human gates at 04d or 04e — those red→green handoffs are automated by quality-gate scripts.

> **Agent stance for the whole of Stage 04:** the spec artefacts
> from 02–03 are now your contract; if a test wants behaviour the
> spec didn't promise, the defect is upstream. Resist the urge to
> "make the test pass" by silently extending a concept's outcome
> enum.

---

## Turn 10 — Stage 05 (Verify and close)

**CONTEXT loaded:** [`features/UC-00-login/stages/05_verify/CONTEXT.md`](../features/UC-00-login/stages/05_verify/CONTEXT.md)

**Inputs opened:**

- `../01_usecase/output/usecase.md` — scenarios to verify against.
- `../03_syncs/output/` — authorising sync rules.
- a flow-token log from a representative test run.
- [`methodology/architecture/FLOW_TOKENS.md`](architecture/FLOW_TOKENS.md).

**Agent action — Part 1 (Verify):** for each scenario, find the root
flow token, walk the parent-linked tree, check each action is
authorised by either a sync `then` or the scenario's trigger. Write
`output/trace.md`. If anything is unauthorised, write `findings.md`
naming the owning stage; **do not proceed to Close** until findings
are resolved.

**Agent action — Part 2 (Close):**

1. **Smoke** the running profile (e.g. `mvn exec:java`); record real
   commands + real responses in `output/smoke.md`.
2. **Tracking** — update the roadmap if the TRACKING overlay is in
   use; otherwise write the single-line `output/tracking.md`
   recording that.
3. **Resume-point** — append a one-line `Resume point:` to the top
   of `trace.md` so the next session has a clean entry.

**Gate behaviour:** any verify finding routes the loop *back* to the
owning stage; closure has no further gate — once Smoke + Tracking +
Resume-point are written, the feature is done.

> **Why this matters downstream:** the `Resume point:` line at the
> top of `trace.md` is the **bridge** to the next feature's Stage 00.
> The next session's first read should land on it.

---

## What this walkthrough is not

- **Not a script.** Real sessions are messier — the human will edit
  outputs in place (treat the edit as authoritative), reject a turn
  ([`AGENTS.md`](../AGENTS.md) §6 rejection protocol), or ask for an
  iterative change ([`core/ITERATIVE_CHANGES.md`](core/ITERATIVE_CHANGES.md))
  that doesn't replay the full 00→05.
- **Not the only example.** UC-00-login is small on purpose. A larger
  feature would have more concepts, more syncs, and more Pattern D
  reads at Stage 03a. The *shape* of each turn doesn't change.
- **Not a substitute for `CONTEXT.md`.** The CONTEXT files are still
  the binding contract; this walkthrough just makes the shape of a
  clean turn easier to recognise.

## How to use this file as an agent

When you start a turn, do this in order:

1. Read this file's matching turn (Turn N for Stage N).
2. Open the stage `CONTEXT.md` it cites and confirm the `Inputs` table
   still matches.
3. Open *only* those inputs.
4. Write *only* into `output/`.
5. Ask the canonical gate question and **stop**.

If your turn would deviate from the matching turn here in a way that
isn't justified by the human's brief or by an explicit instruction,
that is a signal to surface the deviation rather than silently take
it.
