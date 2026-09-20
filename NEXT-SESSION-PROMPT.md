# Fresh-session prompt — CLAD after the Model B experiment

You are picking up CLAD after a long experiment that landed Model B and then ran
a derived app through it end to end. Everything is committed and green in both
repos. Your job is the **four open items at the end**; read this whole brief
first, then `AGENTS.md`, `CONTEXT.md`, and the active feature's `RESUME.md` as
usual.

---

## 1. The repos and their state

**`clad`** — `/Users/alanp/Documents/GitHub/clad`
- Branch `feat/system-scope-concept-vocabulary`, **40 commits ahead of `main`**,
  tree clean. Gate suite **182** green; the whole reference reactor
  (`legible-engine`, `java-legible`, `java-plain`, `java-micronaut-postgres`,
  `legible-bench`) **BUILD SUCCESS**.
- **Not merged to `main`, not tagged, `CHANGELOG.md` has an `[Unreleased]`
  section with no version.**

**`clad-library-lending`** — `/Users/alanp/Documents/GitHub/clad-library-lending`
- The derived experiment. Five features `UC-00`…`UC-04`, **all complete through
  Stage 05**; app suite **60** green; tree clean; pipeline intact.
- In-memory profile. App under `app/` (Maven, `dev.library.lending`), engine
  consumed as `com.example.clad:legible-engine:0.1.0-SNAPSHOT` installed locally
  from clad:
  `mvn install -f reference-impl/pom.xml -pl legible-engine -am -DskipTests`.
- Its `ROADMAP.md` says no follow-up feature is planned; the backlog carries
  item 2 below.

---

## 2. What was built — Model B, in one screen

Concepts are **canonical, system-scope assets**:

- Corpus at `features/_system/concepts/`, **three artefacts per concept** —
  `<Name>.concept.md`, `<Name>.data-model.md`, `<Name>.contract.md` — plus a
  generated `concepts-catalog.md`, a **reviewed** `concept-dependence.md`, and
  `_promotions/<UC>.md` receipts.
- A use case **reuses / extends / proposes**. Proposals enter the corpus only on
  Gate 2 approval via `./clad promote-concepts <feature>` (it requires an
  explicit feature — it writes the corpus, so it never guesses).
- **R22** added (a concept is defined once, in the corpus). R1–R21 unchanged.
- New gates: `verify_concept_registry`, `verify_concept_criteria`,
  `verify_concept_proposals`, `verify_concept_additivity`,
  `verify_concept_corpus_current`, `verify_sync_flow_pin`,
  `verify_shared_triggers_current`; `verify_chain_grammar` now requires the
  stage-01b `stateDiagram-v2`.
- **Grammar v3.1**: names are action-first; a route-scoped **bootstrap** carries
  `For<Route>` (`VerifyForReturnsWhenRequestRouted`); and **flow pinning** —
  every **non-bootstrap** rule names its flow root as its **last** conjunct with
  the route matcher.
- The Stage 04b artefact is the **concept contract** (renamed from SPEC) and is
  canonical too.
- Maintenance records from the experiment, each with design + evidence gates:
  `system-scope-concept-vocabulary`, `concept-owned-data-model`,
  `concept-provenance-and-additivity`, `sync-name-grammar-v3`,
  `route-scoped-sync-names`, `sync-flow-pinning`, `engine-absent-state-guard`,
  `chain-diagram-required-and-joins`, `transport-framing-adapter-owned`,
  `spec-renamed-to-concept-contract`.

**Engine changes** (`reference-impl/legible-engine`): `absent` (a negative state
pattern — `Clause.Absent`, `Dsl.absent`, `WhereEvaluator`), and the empty-safe
aggregate now carries the frame from **before the fan-out chain**.

---

## 3. What the experiment found — the transferable lessons

1. **A superseded proposal overwrote the corpus.** `promote-concepts` defaulted
   to a guessed active feature, targeted one whose RESUME still said `Stage 04c`,
   and replaced the canonical `MemberEnrolment` spec with an older proposal —
   dropping `verify`. Now: explicit feature required; the canonical spec records
   `introduced-by` / `extended-by <UC>, …` (append-only, in promotion order); only
   the concept's **current source** may promote it (per concept, refusing with a
   reason); `verify_concept_corpus_current` ties every Gate-2-approved proposer to
   the history and the receipts.
2. **The two-copy question.** A feature's copy is a **proposal snapshot**; the
   corpus's is **canonical**. File equality is the *wrong* invariant — from the
   second extending use case onward an earlier snapshot is *supposed* to differ.
   Ordering is the right one.
3. **Additivity was social.** `_state_changed` is a *difference* test, so a
   removed state line looked like an added one. Now `verify_concept_additivity`
   (wired to 03b and 04b) refuses a dropped/restated canonical `## State` line or
   contract outcome; a deliberate, bounded removal is listed in
   `_config/additivity-exceptions.md`.
4. **Per-feature gates cannot see cross-UC defects.** Five checkers had to learn
   a shape the work introduced: the contract surface is the **shadowed union**
   with the corpus (a reused concept binds canonically); the corpus-currency and
   shared-trigger views must be **current**; the mechanical sync name **excludes
   the flow pin** and **keeps the bootstrap route**; `--strict-trigger` reads the
   rule's **primary**, not its pin.
5. **Two use cases sharing a completion fired each other's rules.** UC-03's
   `lend` fired in UC-04's return flow and vice versa — the engine's own message
   was the evidence (`expected: <copy is not on loan to this member> but was:
   <copy is not on the shelf>`). Fix: **flow pinning**, the paper's
   `RegistrationError` idiom (§5.3, "other web requests may be in process at the
   same time") and ConceptBox's universal practice ("Multiple When Clauses:
   Handling Request Flows"). **The pin goes LAST**: CLAD's engine dispatches a
   joined rule on its **primary (first)** conjunct's completion, so a pin first
   fires the rule before its own trigger completes and never re-evaluates.
   ConceptBox's `actions([...])` is order-agnostic; its reading order does not
   transfer.
6. **The DSL could not say "the ones that don't have X".** Every `where` source
   enumerates state and `collect` takes no filter. Fix: **`absent`** — a negative
   state pattern, deliberately an *operator* (no computation, no JSON) so R3
   holds, not conceptbox's imperative `filter`.
7. **The empty-safe aggregate carried the wrong frame.** When `absent` filtered a
   non-empty fan-out to nothing, it seeded a **blank** frame, so a rule answered
   `200` with a correct `openLoans: []` and **nulls** for every earlier binding.
   It now carries the frame from **before the fan-out chain** — ConceptBox's
   `const originalFrame = frames[0]`.
8. **A state-changing extend forced a behavioural edit to an existing action.**
   Recording `returnedAt` meant `open`'s guard had to test *openness* ("at most
   one loan without a `returnedAt`"), not the existence of a loan. Invisible at
   the contract level; the concept test caught it.

---

## 4. Operational lessons — do not relearn these

- **Order of operations in a feature:** finish the stage → `./clad advance` →
  **commit** → `./clad verify`. Uncommitted `*.sync.md` / `*.concept.md` make
  `verify_iterative_change_readiness` demand an active `_changes/` record.
- **Exactly one** `**Status:** active` record under a feature's `_changes/` while
  its sync/concept artefacts are uncommitted.
- **`_changes/` field values must be only the backticked token** —
  `` - **Earliest re-entry stage:** `03` ``. Trailing prose breaks the parser
  (same for `Feature-contract impact`, `Status`, `Change class`).
- **One rule per method in the app.** `verify_sync_implementation_parity` needs a
  literal `rule("Name")`; a shared helper that takes the name as a parameter
  fails it.
- **Gate coverage:** Gate 1 = 01–01b, Gate 2 = 02–03b, Gate 3 = 04a–04c.
  Renaming or adding a sync spec invalidates **Gate 2**; editing a chain note
  invalidates **Gate 1**; 04b/04c edits invalidate **Gate 3**.
- **When a value is mysteriously null, print it.** Substituting sources
  (`triggerField` / `conjunctField` / `siblingField`) burned most of a session;
  binding a **literal** and printing the response found the root cause in one run.
- **A checker that fails on a new shape is usually the checker.** Five needed
  teaching here; prefer fixing the checker (with a test) over contorting the
  artefact.

---

## 5. The four open items

### Item 1 — Merge and version the clad work

40 commits on a branch, no release, `CHANGELOG` unreleased.

- Review the diff against `main` (`git log main..HEAD --oneline`), confirm the
  branch is green end to end, then merge per `methodology/implementation/DELIVERY.md`.
- Decide the version with the human (the `[Unreleased]` section has ~6 entries:
  Model B, the SPEC→contract rename, grammar v3.1 + route-scoped names, flow
  pinning, `absent`, the aggregate fix). Tag per AGENTS.md rule 16 — **only with
  explicit human authorisation.**
- Acceptance: `main` green (gate suite + full reactor), a versioned CHANGELOG
  section, an annotated tag.

### Item 2 — The experiment's three backlog items

All three are in `clad-library-lending/ROADMAP.md`. Each needs its own change;
none could be folded into UC-04.

- **2a. `Stocking.acquire` accepts a negative count** — `copies: -1` mints
  nothing yet reports `acquired`. `copies: 0` is legal and tested. A fix needs a
  new outcome **and** a transport branch, so it is a **UC-02 re-entry** (chain
  table → sync → response), not a retroactive edit.
- **2b. Pinned rules still share names across use cases.** Pinning made UC-03's
  and UC-04's refusal rules genuinely distinct (same trigger and target,
  different route) and both are registered — but they share a name, so
  `causedBySync` cannot say which fired. The uniform fix is to scope **every**
  pinned rule's name by its route (~25 renames in both repos, plus Gate 2
  re-approvals). A collision-dependent rule was rejected as non-derivable.
- **2c. `absent` under a durable store is untested.** The clause resolves through
  `Region.read`, which `RmapPostgresFactStore`/`PostgresFactStore`/`JenaFactStore`
  all implement, but nothing exercises it there, and an optional relation like
  `returnedAt` has no `NOT NULL` story (`V1__login_rmap.sql` explains why
  mandatory roles are not emitted as `NOT NULL`). Stage 04a's conditional
  relational gate (`verify_relational_mapping`) has never run.

### Item 3 — Methodology follow-ups

- **Readiness-guard ordering** (see §4): consider making it distinguish new stage
  work from an edit of gated artefacts, so `advance → commit → verify` is not
  required.
- **"Checker learns late" is systemic.** Five checkers failed on shapes the pin
  introduced, each discovered only when a feature reached the gate. Worth a pass:
  for every checker that reads contracts/specs, ask "does it know about the
  corpus union, the flow pin, and route-scoped names?" and add tests.
- **Canonical concept *proposals* are not provenance-stamped.** The corpus
  spec/model/contract carry `introduced-by` / `extended-by` and a canonical
  header; the feature-local proposal in `02_concepts/output/` is stamped only by
  the generator, and a hand-authored proposal carries nothing. Consider a stamp
  at authoring time (`templates/concept.md`).

### Item 4 — Review the flow-pin rule (do this first)

It is the largest semantic change in the experiment: it narrows when **every**
non-bootstrap rule fires, in both repos. It is source-backed and fully tested,
but it is the change most likely to have a case nobody thought of.

- Read `maintenance/sync-flow-pinning.md`, then the §"Flow pinning" section of
  `methodology/architecture/SYNCHRONIZATIONS.md`.
- Check the interactions: a rule that legitimately needs to fire in **two** flows
  (the pin says "one rule, one flow" — is that always right?); a flow with more
  than one `Web/request`; a sync whose trigger is a *shared* completion and whose
  target is shared too (2b is the name half of that); and whether the pin should
  be validated against the *chain* (the generator derives it from row 1's route).
- Acceptance: either a written finding that the rule holds, or a narrowed rule
  with tests. Do not merge item 1 before this is settled.

---

## 6. Where to look

| What | Where |
|---|---|
| Rules (R1–R22) | `methodology/implementation/RULES.md` |
| Stage map, gates, advance mechanics | `methodology/implementation/STAGES.md` |
| Concept anatomy, corpus model, proposal vs canonical | `methodology/architecture/CONCEPTS.md` |
| Sync semantics, flow pinning, joins, `collect` | `methodology/architecture/SYNCHRONIZATIONS.md` |
| Data-flow patterns (A/B/C/D, `absent`) | `methodology/architecture/SYNC_PATTERNS.md` |
| The four open items' reasoning | `maintenance/sync-flow-pinning.md`, `maintenance/route-scoped-sync-names.md`, `maintenance/engine-absent-state-guard.md`, `maintenance/concept-provenance-and-additivity.md` |
| The experiment's closure | `clad-library-lending/features/UC-04-return-copy/stages/05_verify/output/trace.md` (resume point at the top) |
| Experiment backlog | `clad-library-lending/ROADMAP.md` |
