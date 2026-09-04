# Hard rules

These rules are non-negotiable. Violating any of them in code, specs, or
stage outputs is a defect. An agent that suspects a request would
require violating one of these must **stop and surface the conflict**
rather than relax the rule.

> **This file is the authoritative text.** `AGENTS.md` §"Hard rules"
> carries only a compact index and defers here. R1–R9 are the nine
> original rules; R10–R21 are hard-learned additions. R10 and R21 are
> retired — their IDs are kept only so an audit that greps for them
> finds the retirement note, not a live obligation.

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

This rule is *enforceable* structurally in the canonical profile: each
concept receives its own `Region` from the `FactStore` (one region per
concept name) and can never touch another concept's region.

## R3. Syncs are declarative, not imperative

A sync has the form `when … where … then …`. It does not contain
business branching, state, or I/O. See
[`../architecture/SYNCHRONIZATIONS.md`](../architecture/SYNCHRONIZATIONS.md).

If a sync wants to say `if x then A else B`, the discrimination must
be lifted into a concept whose action returns one of two outcomes,
matched by two separate syncs.

## R4. One primary bootstrap adapter owns each transport surface

For each transport surface, exactly one primary bootstrap adapter owns the
entry/exit actions. The HTTP/RPC convention is `Web`; other transports may use
an equivalent such as `Grpc`, `Stream`, or `Cli`. No business concept defines
routes, controllers, handlers, or transport consumers. Inbound signals become
bootstrap actions, which fire syncs into business concepts. See
[`../architecture/WEB_CONCEPT.md`](../architecture/WEB_CONCEPT.md) and the
optional [`../overlays/PORTS_AND_ADAPTERS.md`](../overlays/PORTS_AND_ADAPTERS.md)
for the transport-neutral boundary rules.

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

## R10. *(retired)* Sync SPARQL variables MUST use the engine's reserved names

> **Retired** with the fire-after-commit engine. The RDF/SPARQL engine's
> reserved variables (`?_when_1`, `?_flow`, `?_then_1`) no longer exist:
> syncs are declarative `SyncRule` `when/where/then` rules with explicit
> named-argument bindings, and the flow token is an explicit record field.
> No equivalent hazard remains.

## R11. Every sync that fires on a shared business-concept action MUST filter by route

A shared business-concept action (e.g. `Session/grant[GRANTED]`) fires
for login, sign-in, AND register flows. If a respond sync does not
declare its route scope (a `where`-clause `Guard` binding the request
route from the `Web/request` input), it fires for all three flows,
producing wrong HTTP status codes (e.g. login returning 200 instead of
register's 201). Syncs that trigger on `Web/request` already carry the
route in their trigger input — others MUST add a route `Guard`.

## R12. A concept action MUST write a named `outcome` field

The engine's dispatch loop skips an action that already has a completion
record; a completion is identified by the presence of an `outcome` field
in the returned map. Without it, an action is re-processed on the next
drain (duplicate registrations, runaway sync firing). The completion
record carries the `outcome` plus the action's named fields; syncs match
on `outcome` in their `when` clause.

## R13. Jackson must serialize null values (`Include.ALWAYS`)

CLAD syncs author field-value maps where missing fields imply null.
Jackson's default `NON_NULL` omits these fields, making Conduit spec
assertions like `jsonpath "$.user.bio" == null` fail with `none` not
`null`. Configure `jackson.serialization-inclusion: always` in
`application.yml` or equivalent for your profile. See `clad.properties`
for the canonical setting.

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

A concept action's completion map carries named fields that downstream
syncs consume. If a field-mapping bug exists (wrong key name, missing
binding, value collision), an outcome-only test will pass while
all downstream consumers receive null or empty values.

Stage 04d red tests must therefore include field-value assertions for
every primary completion field that downstream syncs read.

## R17. Every change to a sync or concept MUST re-enter the CLAD stage pipeline

`methodology/core/ITERATIVE_CHANGES.md` is binding. Before modifying any
file under:

- `features/UC-*/stages/02_concepts/output/` (concept specs)
- `features/UC-*/stages/03_syncs/output/` (sync specs)
- any profile's implementation source for concepts or syncs
  (e.g. `reference-impl/java-legible/src/main/java/dev/legible/example/.../`
  (canonical profile), or `reference-impl/java-micronaut-jena/src/.../{concepts,syncs}/`
  (legacy profile))

the agent MUST:

1. Open `methodology/core/ITERATIVE_CHANGES.md` and classify the change
   (Presentation / Behavioural / Structural).
2. Identify the earliest stage whose `output/` is no longer accurate and
   re-enter there.
3. Update all affected stage artefacts (sync specs, concept specs, chain
   tables) in the **same commit** as the implementation change.

A Java sync class with no corresponding `*.sync.md`, or a Java concept
class whose outcomes no longer match the approved `*.concept.md`, is a
defect of the same severity as a cross-concept import (R1).

Mechanised by `quality-gate/verify_implementation_parity.py`
(implementation→artefact), `verify_sync_implementation_parity.py`
(artefact→implementation), `verify_iterative_change_readiness.py`
(intake), and `verify_iterative_change_coupling.py` (same-batch).

## R18. The quality gate is mandatory at commit time

`git commit --no-verify` is forbidden in a CLAD workspace. The
pre-commit hook runs deterministic checks (stage sequence,
iterative-change coupling). If it blocks a commit, the defect is real —
a stage was skipped or code is decoupled from its spec. The only
acceptable bypass is `CLAD_HOOK_SKIP=1`, and only under explicit human
instruction.

## R19. `test.command` is the sole valid test invocation

The command in `clad.properties` runs the artefact pipeline gate
(`verify_artefacts.py`) before any profile tests. Running the test
framework directly (e.g. `mvn test` by itself) skips artefact
verification and produces invalid feedback — tests may pass while stage
artefacts are stale. Always use the full command from `clad.properties`.

## R20. Engine and profile maintenance changes require maintenance governance

Changes to engine/runtime sources, profile configuration/resources,
Docker or Compose files, and root `clad.properties` that preserve the
approved feature contract do not invent a new UC or re-run Stage 00.
Before changing those surfaces, create `maintenance/<change-name>.md`
from `templates/maintenance-change.md`, obtain the design-gate approval,
and test against explicit runtime invariants. Obtain evidence-gate
approval before commit. If the change alters an action outcome, response
contract, concept boundary, sync rule, flow-token lineage, or observable
action order, also re-enter the earliest affected feature stage under
R17.

Mechanised by `quality-gate/verify_maintenance_change_readiness.py`.

## R21. *(retired)* RDF-star/SPARQL-star patterns MUST use Jena programmatic APIs

> **Retired** with the fire-after-commit engine. RDF-star/SPARQL-star is
> gone entirely: facts are relation-shaped (`FactStore`/`Region`), the
> action log is a structured append-only record store, and there is no
> SPARQL to construct. The strict-vs-lenient parser hazard this rule
> guarded against no longer exists.

---

Six of these rules — R1, R3, R8, R9, R14, and R15 — fail most often by
accident. When reviewing PRs, look for them first.
