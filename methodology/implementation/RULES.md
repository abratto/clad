# Hard rules

These rules are non-negotiable. Violating any of them in code, specs, or
stage outputs is a defect. An agent that suspects a request would
require violating one of these must **stop and surface the conflict**
rather than relax the rule.

## R1. No concept imports or references another concept

In code (under `reference-impl/`):

- No `import` across concept packages.
- No shared base classes or interfaces between concepts (a sync can
  define an interface, but two concepts must not implement the same
  one for the purpose of cross-talk).
- No shared mutable singletons.

In specs (under `features/UC-XX/stages/02_concepts/output/`):

- A concept spec may not name another concept's state field.
- A concept spec may name *types* that are passed in as opaque
  identifiers (`UserId`, `SessionId`); it may not name another
  concept's *actions*.

If two concepts seem to *need* to reference each other, that is a sign
either that one of them is doing too much (split it) or that the
coordination belongs in a sync.

## R2. One named persistence region per concept

When concepts persist state and the storage technology supports it
(named graphs in RDF, schemas in SQL, separate document collections),
each concept owns exactly one region and reads only from that region.
Cross-region reads are a violation.

This rule is *enforceable* in the Java/Jena profile via per-concept
graph URIs.

## R3. Syncs are declarative, not imperative

A sync has the form `when … where … then …`. It does not contain
business branching, state, or I/O. See
[`../architecture/SYNCHRONIZATIONS.md`](../architecture/SYNCHRONIZATIONS.md).

If a sync wants to say `if x then A else B`, the discrimination must
be lifted into a concept whose action returns one of two outcomes,
matched by two separate syncs.

## R4. `Web` (or equivalent) is the sole HTTP entry

Exactly one concept owns the HTTP/RPC surface. By convention it is
called `Web`. No other concept defines routes, controllers, or HTTP
handlers. Inbound requests become `Web.handle(...)` calls, which fire
syncs into business concepts.

## R5. Every action emits a flow token

Every public action of every concept emits exactly one flow token at
completion (success *or* failure outcomes). Tokens are linked via
`parent` to their cause. See
[`../architecture/FLOW_TOKENS.md`](../architecture/FLOW_TOKENS.md).

This is what makes `stages/05_verify/` possible.

## R6. Stage outputs are written only by the owning stage

`features/UC-XX/stages/03_syncs/output/` is written only by the agent
running stage 3, or by a human reviewing it. Stage 4 reads from it
but does not write back. If stage 4 would need to amend a sync, it
returns to stage 3 with the amendment as input and re-runs.

## R7. Every running effect traces back to a use case

The chain `flow-token → sync → concept-action → use-case-scenario` must
be walkable for every observable effect. If you find an effect that
does not back-trace, you have either an unauthorised behaviour (fix the
code) or an incomplete use case (amend the contract).

## R8. Outer-loop tests before implementation — inner loops are derived

In Stage 04c, flow tests (Gherkin `.feature` files) are the executable
form of the use case. They must be written, reviewed, and approved by
the human before any implementation begins. This is Gate 3 (Executable
specification) — the last design-stage human gate.

In Stages 04d and 04e, concept tests and sync tests are **mechanically
derived** from already-approved artefacts (04c flow tests, 04b SPECs,
chain tables, sync specs). They verify implementation fidelity, not
design. The red→green handoff in 04d and 04e is automated — the
quality-gate scripts (`verify_concept_test_derivation.py`,
`verify_sync_matrix.py`) serve as the gate. No human approval is
required at these inner boundaries.

An agent that writes concept or sync implementation before the
corresponding red tests exist has violated this rule. The flow test
(04c) must be approved before any inner loop begins.

## R9. Every SPEC outcome maps to a distinct implementation branch

In implementation code, each outcome defined in the SPEC must be
returned by its own distinct code path. Two SPEC outcomes must never
be collapsed into one return value (e.g. returning `VALIDATION_FAILED`
when the SPEC defines `ACCOUNT_EXISTS` as a separate outcome).

If you find yourself returning one outcome for two different
conditions, check the SPEC — they are almost certainly distinct
outcomes that were defined separately for a reason.

**Outcome branching checklist** — verify before claiming green:

- [ ] Each SPEC outcome has its own `if` / `switch` branch — not shared with another outcome
- [ ] Each branch returns the correct `OutcomeType` enum value
- [ ] `message` is null on success outcomes, non-null on failure outcomes
- [ ] `id` fields are non-null on creation success outcomes, null on failure outcomes
- [ ] `refusalReason` is non-null on refused outcomes, null on success/error outcomes
- [ ] Numeric status codes match the approved chain-table row exactly — no type coercion
- [ ] No two constructor signatures or methods with the same erasure (Java compile error)

## R14. Concept unit tests assert field values, not only outcome tokens

Every concept unit test must assert the action outcome and the primary
fields written by `writeCompletion`. A test that only checks
`outcome == "FOUND"` is insufficient because downstream syncs consume
the named completion fields, not the outcome token alone.

At minimum, a concept unit test asserts:

- The `outcome` value.
- The primary output fields written by the concept action.
- No primary output field is null or an empty string when inputs are
  valid.

## R15. Shared-trigger syncs declare route scope

A sync whose trigger action can be produced by more than one named
flow/route must either carry an explicit route filter or document why
route-agnostic firing is correct. Stage 03a records this in the
dependency review cards.

A sync that fires on a shared trigger without a route filter or explicit
route-agnostic justification is a defect.

## R16. Stage 04d tests assert completion field values

`writeCompletion` writes named fields that downstream syncs consume. If
a field-mapping bug exists (wrong variable name, PSS substitution
collision, missing SPARQL binding), an outcome-only test will pass while
all downstream consumers receive null or empty values.

Stage 04d red tests must therefore include field-value assertions for
every primary completion field that downstream syncs read.

---

Six of these rules — R1, R3, R8, R9, R14, and R15 — fail most often by
accident. When reviewing PRs, look for them first.
