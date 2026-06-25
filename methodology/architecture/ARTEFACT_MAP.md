# ARTEFACT_MAP.md — what each artefact is, who produces it, who consumes it

This file is the **dependency graph** of CLAD's per-feature artefacts.
It exists so that humans and agents can answer two questions without
re-reading every stage's `CONTEXT.md`:

1. *"If I change `<artefact>`, what downstream work has to be redone?"*
2. *"If I'm asked to produce `<artefact>`, what upstream artefacts do I
   need open in front of me, and what specifically am I extracting from
   each?"*

It is a Layer 3 (stable) reference. The per-stage `CONTEXT.md` files
are still the authoritative contracts; this file just makes the
**graph between them** legible.

---

## 1. The diagram

```
[ human brief ]
       │
       ▼
┌──────────────────────┐
│ 00_actor-goal/       │   actors.md, goals.md
└──────┬───────────────┘
       │ (in-scope actor + goal list)
       ▼
┌──────────────────────┐
│ 01_usecase/          │   usecase.md   ◄────────────────────────────┐
└──────┬───────────────┘                                             │
       │ (named scenarios + Postconditions)                          │
       ├──────────────────────────────┐                              │
       ▼                              ▼                              │
┌──────────────────────┐   ┌──────────────────────┐                  │
│ 02a_responsibility-  │   │ 02b_chain-table/     │                  │
│   map/               │   │ <scenario>-chain.md  │                  │
│ responsibility-      │   │ (one per scenario)   │                  │
│   map.md             │   └──────┬───────────────┘                  │
└──────┬───────────────┘          │ (canonical action names +        │
       │ (concept set + state +   │  outcome enums)                  │
       │  action names)           │                                  │
       └────────────┬─────────────┘                                  │
                    ▼                                                │
        ┌──────────────────────┐                                     │
        │ 02_concepts/         │   <Name>.concept.md (one per row    │
        │                      │     in the responsibility map)      │
        └──────┬───────────────┘                                     │
               │ (state, actions, outcomes, flow-token shape, R1)    │
               ├───────────────────┐                                 │
               ▼                   ▼                                 │
   ┌──────────────────────┐ ┌──────────────────────┐                 │
   │ 03_syncs/            │ │ (used directly by)   │                 │
   │ <name>.sync.md       │ │   04a, 04b, 04d      │                 │
   │ when … where … then  │ └──────────────────────┘                 │
   └──────┬───────────────┘                                          │
          │ (every then-call + every Pattern A/B/C/D where-clause)   │
          ▼                                                          │
   ┌──────────────────────┐                                          │
   │ 03a_dependency-      │   <concept>-card.md + pattern-d-         │
   │   review/            │     summary.md                           │
   └──────┬───────────────┘                                          │
          │ (cross-concept coupling surface; Pattern D field list)   │
          ▼                                                          │
   ┌──────────────────────┐                                          │
   │ 03b_data-model/      │   <Name>.data-model.md                   │
   └──────┬───────────────┘                                          │
          │ (conceptual facts + constraints per concept)             │
          ▼                                                          │
   ┌──────────────────────────────────────────────────┐              │
   │ 04_implement/  (router → 5 sub-stages)           │              │
   │                                                  │              │
   │  04a_storage-mapping/  data model → profile      │              │
   │                       storage mapping            │              │
   │  04b_spec/   concept spec → SPEC slice           │              │
   │  04c_flow-tests/   one outer-red flow test per   │              │
   │                    scenario  ────────────────────┼──┐           │
       │  04d_concept-tdd/  router -> 04d_red-tests,      │  │           │
       │                    04d_green-impl                │  │           │
       │  04e_sync-tdd/     router -> 04e_red-tests,      │  │           │
       │                    04e_green-impl; outer flow    │  │           │
       │                    tests go GREEN ───────────────┼──┘           │
   └──────┬───────────────────────────────────────────┘              │
          │ (compilable artefact + green test suite)                 │
          ▼                                                          │
   ┌──────────────────────┐                                          │
   │ 05_verify/           │   trace.md (back-trace of every          │
   │                      │     observed flow token to a scenario)   │
   │                      │   findings.md (defects route upstream) ──┘
   │                      │   smoke.md, tracking.md (closure)
   └──────┬───────────────┘
          │
          ▼
   resume-point (at top of trace.md) ──► next feature's Stage 00
```

Key edges to notice:

- **Use case is the contract every later stage cites.** The dashed
  back-edges from 02a, 02b, 02, 03, 04c and 05 all land on
  `usecase.md`. That is what makes the loop *contract-driven*.
- **Chain tables (02b) win over sync specs (03)** when action names
  disagree — because 03 cites 02b, not the other way around. (See
  PR #6 — `Session.open` reconciled to `Session.grant`.)
- **03a is a pure-audit stage.** It has *no* downstream artefact of
  its own except the cards and summary; its value is making coupling
  visible *before* code at 04 ossifies it.
- **04c is the outer red, 04e closes it.** Nothing else makes the
  flow tests go green; that is the whole point of separating 04d
  from 04e.
- **05 has two halves.** *Verify* back-traces (loop closure); *Close*
  smoke-tests + writes the resume-point that becomes the next
  feature's bridge.

---

## 2. Per-artefact table

Each row answers: **what is it, who produces it, who consumes it,
what specifically does the consumer read out of it, and why does the
consumer need that?**

| Artefact | Produced by | Consumed by | What the consumer needs from it | Why |
|---|---|---|---|---|
| `actors.md` | 00 | 01 | Verbatim actor list | The use case's *Actors* section must match — no inventing actors after Stage 00. |
| `actors.md` | 00 | 02a | Set of in-scope actors | Coverage check: every in-scope actor must be represented by ≥1 concept. |
| `goals.md` | 00 | 01 | In-scope goal list | Each in-scope goal becomes ≥1 named scenario. |
| `goals.md` | 00 | 01 | Out-of-scope goal list | Lifted into the use case's *Out of scope* section verbatim. |
| `usecase.md` | 01 | 02a | Set of named scenarios | The responsibility map's *Coverage check* asserts every scenario is covered by ≥1 concept. |
| `usecase.md` | 01 | 02b | One named scenario per chain file | One chain table per scenario; trigger and final response must match. |
| `usecase.md` | 01 | 02 | Scenario names + Postconditions | Each concept's *operational principle* must reference these scenarios; the principle is what 04d tests against. |
| `usecase.md` | 01 | 03 | Scenario names | Every sync's `Cites` block names a scenario it satisfies. |
| `usecase.md` | 01 | 04c | Scenarios + Postconditions—Success/Failure | One outer-red flow test per scenario; Postconditions are what the test asserts (including the *no state is modified* assertion that mechanises no-enumeration). |
| `usecase.md` | 01 | 05 | Full scenario set | The verifier walks each scenario's flow-token tree; any unauthorised observed action is a finding. |
| `responsibility-map.md` | 02a | 02b | Concept set + action names per concept | The chain table may only reference these concepts and these actions. |
| `responsibility-map.md` | 02a | 02 | Concept set | One `<Name>.concept.md` per row. |
| `responsibility-map.md` | 02a | 03a | Concept set | One dependency-review card per concept. |
| `<scenario>-chain.md` | 02b | 02 | Action names + outcome enums per concept | Concept spec must declare every action used in any chain, with the same outcome enum. **Canonical** when a sync spec disagrees. |
| `<scenario>-chain.md` | 02b | 03 | Per-row links | Each row formalises into a sync `when` (the upstream outcome) → `then` (the downstream call). |
| `<scenario>-chain.md` | 02b | 03a | Inbound calls per concept | Section 1 of each card is built from these. |
| `<scenario>-chain.md` | 02b | 04c | End-to-end action sequence | The flow test asserts exactly this sequence at runtime. |
| `<Name>.concept.md` | 02 | 03 | Action signatures + outcome enums | `when` and `then` clauses reference these. |
| `<Name>.concept.md` | 02 | 03a | Action existence + state field declarations | Cards cite action names; Pattern D rows cite state fields. |
| `<Name>.concept.md` | 02 | 04a | `state` section | The schema is derived from this; one named region per concept (R2). |
| `<Name>.concept.md` | 02 | 04b | Action signatures + outcome enums + flow-token shape | Mechanically extracted into the SPEC slice. |
| `<Name>.concept.md` | 02 | 04d | Operational principle + per-action effect on state | The TDD red tests are derived from these. |
| `<name>.sync.md` | 03 | 03a | Every `then` call + every `where` clause | Tabulated per concept (cards), with Pattern A/B/C/D labelled. |
| `<name>.sync.md` | 03 | 04c | Expected coordination chain | Flow test's expected token sequence comes from here. |
| `<name>.sync.md` | 03 | 04e | `when … where … then` | One inner red→green TDD pass per sync. |
| `<name>.sync.md` | 03 | 05 | Authorisation surface | The verifier checks every observed call is authorised by either a sync `then` or a use-case scenario trigger. |
| `<concept>-card.md` | 03a | 03b | Pattern D fields owned by this concept | Drives conceptual data-model coverage (the field must be exposed in this concept's region). |
| `<concept>-card.md` | 03a | 04b | Full inbound contract for this concept | The SPEC author sees every call this concept will receive. |
| `<concept>-card.md` | 03a | 04d | Inbound action surface | The concept TDD knows what its boundary actually is. |
| `<concept>-card.md` | 03a | 04e | Set of concepts this sync invokes | The sync TDD knows which concepts to double. |
| `pattern-d-summary.md` | 03a | 03b | Single cross-cutting list of every Pattern D read | One conceptual data-model checklist for the whole feature. |
| `<Name>.data-model.md` | 03b | 04a | Approved fact types and constraints | The storage mapping must realize this model without drift. |
| `<Name>.storage.md` (or `_NOT_APPLICABLE.md`) | 04a | 04d | Storage shape for the test fixture | The concept TDD builds against this mapping when persistence exists. |
| `<Name>.spec.md` | 04b | 04c, 04d, 04e | Action signatures the test code compiles against | All inner-loop and outer-loop tests reference SPECs, not prose. |
| `<feature>.feature` + `<Feature>StepDefinitions.java` | 04c | 04e | The flow test that must go green | When the last sync goes green, the flow test must too. |
| `<feature>.feature` + runner | 04c | 05 | Expected runtime token chain + Gherkin scenarios | The back-trace evidence comes from running this. |
| `concept-test-derivation.md` | 04d | 04e | What concept actions are already-green | The sync TDD relies on these as its substrate. |
| `concept-test-derivation.md` | 04d | 05 | Test coverage map for actions | Distinguishes "covered by unit test" from "covered only by flow test." |
| `<Name>ConceptTest.java` + `<Name>Concept.java` | 04d | 04e, 05 | Running concept layer | The substrate the syncs orchestrate; the back-trace target. |
| `sync-test-derivation.md` | 04e | 05 | Test coverage map for syncs | Same purpose as the concept derivation map, for syncs. |
| `<SyncName>Test.java` + `<SyncName>.java` | 04e | 05 | Running coordination layer | This is the artefact 05 back-traces against. |
| `trace.md` | 05 | next feature's 00 | `Resume point:` line at the top | The bridge between features. |
| `findings.md` | 05 | upstream stage(s) | Defects, with the owning stage named | Routes work back, never forward. |
| `smoke.md` | 05 | (the human) | Real recorded commands + responses | Proves the *deployable* artefact (not just tests) behaves. |
| `tracking.md` | 05 | (the human / overlay) | Closure note | Even "Not applicable" is a recorded close. |

---

## 3. Where these artefacts live in the running code

CLAD's spec artefacts (`*.concept.md`, `*.sync.md`, …) all map onto
runtime artefacts in the chosen profile:

| Spec artefact | Java reference profile counterpart | Enforced by |
|---|---|---|
| `<Name>.concept.md` `state` | `<Name>Concept` class fields + (optional) `<Name>.data-model.md` + `<Name>.storage.md` | ArchUnit: no field of a concept class is referenced from another concept package. |
| `<Name>.concept.md` actions | public methods on `<Name>Concept`, each emitting a flow token | ArchUnit + R1 + R5. |
| `<name>.sync.md` `when … then` | `<SyncName>` class registered with the sync engine | R3 — no imperative branching inside a sync class. |
| `<scenario>-chain.md` | `<Scenario>FlowTest` (an HTTP-level test) | The chain's row sequence equals the test's expected token sequence. |
| `usecase.md` Postconditions—Success | flow test assertions on response + state | The flow test fails if a Postcondition is unmet. |
| `usecase.md` Postconditions—Failure (*"no state is modified"*) | flow test assertion that no concept's state changed across the request | What mechanises no-enumeration on negative paths. |

See [`reference-impl/java-micronaut-jena/README.md`](../../reference-impl/java-micronaut-jena/README.md)
for the actual mappings, and [`MENTAL_MODEL.md`](MENTAL_MODEL.md) for
the OO ↔ WYSIWID intuition.

---

## 4. How to use this file

**As an agent mid-stage:** before producing your stage's output, scan
the table above for *every row whose "Produced by" matches your stage*
and confirm you can write down the value of "What the consumer needs
from it" in concrete terms for each downstream consumer. If you can't,
you are about to produce an output that will fail a downstream
cross-stage check.

**As an agent reviewing an iterative change:** find the artefact the
change touches in the table, then walk every row whose "Consumed by"
mentions a downstream stage. Each such row is a candidate
re-derivation. (See also
[`../core/ITERATIVE_CHANGES.md`](../core/ITERATIVE_CHANGES.md).)

**As a human onboarding:** read `usecase.md`, then walk down the
diagram in §1 with one of the worked-example artefacts open per stage
(see [`../../features/UC-00-login/README.md`](../../features/UC-00-login/README.md)).
