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
| `outcome` | enum | The action's outcome variant (`Ok`, `InvalidPassword`, …) |
| `payload` | object | Action-specific, redacted as appropriate |

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

## Cost

Emitting a flow token per action is not free, but it is small (a few
hundred bytes, append-only) and is the price of the auditability
property the methodology buys. Implementations are free to sample in
non-production environments; production should not sample.
