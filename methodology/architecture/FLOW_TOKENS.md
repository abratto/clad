# Flow tokens

A **flow token** is a small, structured record emitted by every concept
action. It is the smallest unit of provenance in a WYSIWID system. Flow
tokens are what make the verification stage (`05_verify/`) possible:
they are how a runtime effect is traced back to the use case that
authorised it.

## Required fields

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Unique within the run (e.g. UUID) |
| `parent` | string \| null | The flow token that *caused* this one (e.g. the `Web.handle` that triggered the chain), or `null` for roots |
| `action` | string | `<ConceptName>.<actionName>` |
| `actor` | string \| null | Who initiated the chain (typically a `userId`); flows down from the root |
| `at` | timestamp | When the action completed |
| `outcome` | enum | The action's outcome variant — see **Outcome casing** below |
| `payload` | object | Action-specific — see **Payload rules** below |

## Outcome casing

**Outcome values MUST use SCREAMING_SNAKE_CASE**, matching the Java
enum variant name exactly. Examples: `VALID`, `ACCOUNT_EXISTS`,
`VALIDATION_FAILED`, `CREATED`, `ROUTED`, `SENT`.

PascalCase variants (e.g. `AccountExists`, `ValidationFailed`) are
wrong and will fail cross-stage consistency checks in Stage 05.

When writing flow test specs (Stage 04c), copy outcome values directly
from the SPEC slice (`04b_spec/output/`) — do not invent casing.

## One token per invocation

**Each concept action emits exactly one flow token.** Internal steps
within an action — such as a duplicate-check query inside
`Account.validate` — are implementation details and must not appear as
separate tokens in the chain.

If a chain table row lists `Account.validate`, exactly one
`Account.validate` token appears in the flow token tree for that
invocation. A second `Account.validate` token (e.g. `AccountNotFound`
as an intermediate step) is a phantom token and is always wrong.

The token count for a scenario equals the number of rows in its chain
table, no more.

## Payload rules

The `payload` field is subject to three constraints:

1. **No secrets.** Passwords, tokens, private keys, and any other
   credential MUST NOT appear in any flow token payload. Ever. Flow
   tokens are persisted; a password in a token is a password in a log.

2. **Minimum necessary.** Include only the fields needed to diagnose
   the outcome. For a `VALIDATION_FAILED` outcome, include the field
   names and error messages — not the raw submitted values of sensitive
   fields.

3. **No cross-concept state.** Payload fields must come from the
   concept's own state or from the action's input parameters. A concept
   must not read another concept's named region to populate its token
   payload (R2).

## Why "tokens" and not just "logs"

Logs are best-effort and often free-form. Flow tokens are:

- **Mandatory** — emitted by every action, no exceptions.
- **Structured** — typed fields the verification stage can pattern-match.
- **Linked** — `parent` chains form a tree per request, so any leaf can
  be walked back to its root.

The result is that a question like *"what use case authorised this side
effect?"* has a deterministic answer: walk parent links until you hit a
root token, look at its `action` (`Web.handle <route>`), and ask which
use-case scenario routed there.

## Where they live

In production, flow tokens are typically appended to a structured log
(JSON lines, a relational table, an RDF graph — any store that supports
queryable retrieval by `id` and `parent`). The choice of store is an
implementation detail; the *contract* — that every action emits one and
that they form a parent-linked tree — is what matters.

The Java/Micronaut/Jena reference profile under `reference-impl/` will
land flow tokens in an RDF graph queryable by SPARQL. That is one valid
choice; it is not the only one.

## In stage `05_verify/`

The verifier reads the use case (`stages/01_usecase/output/usecase.md`),
extracts the named scenarios, and for each scenario:

1. Finds the root flow token (the `Web.handle` matching the scenario's
   trigger).
2. Walks the tree of children.
3. Checks that the chain matches the syncs declared in
   `stages/03_syncs/output/`.
4. Checks that no action appears in the chain that is not authorised
   by either a use-case scenario or a sync rule.

A failure at step 4 is a *legibility violation*: the running system did
something its specs did not say it would. Either the specs are
incomplete (amend them) or the implementation drifted (fix it).

## Relationship to the Meng & Jackson paper

The paper mentions flow tokens abstractly in its architectural sections
(6.3 Scoping via Flows, 6.6 Provenance and Firing Consistency) as the
mechanism for associating action records with a causal chain. CLAD
extends this concept with a concrete 7-field structure (`id`, `parent`,
`action`, `actor`, `at`, `outcome`, `payload`) and the SCREAMING_SNAKE_CASE
outcome-casing rule — details the paper does not constrain.

## Cost

Emitting a flow token per action is not free, but it is small (a few
hundred bytes, append-only) and is the price of the auditability
property the methodology buys. Implementations are free to sample in
non-production environments; production should not sample.
