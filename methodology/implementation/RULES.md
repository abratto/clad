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

---

Two of these rules — R1 and R3 — fail most often by accident. When
reviewing PRs, look for them first.
