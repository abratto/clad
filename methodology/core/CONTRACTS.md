# Contracts

A **contract** in CLAD is a small, reviewable specification that authorises
a class of changes. Code that is not authorised by a contract is, by
definition, off-discipline.

## What counts as a contract

| Contract | Lives in | Authorises |
|---|---|---|
| **Use case** | `features/UC-XX/stages/01_usecase/output/usecase.md` | Everything inside the feature |
| **Concept spec** | `features/UC-XX/stages/02_concepts/output/*.concept.md` | The state machine that becomes a concept implementation |
| **Sync spec** | `features/UC-XX/stages/03_syncs/output/*.sync.md` | A coordination rule between concepts |
| **Stage `CONTEXT.md`** | `features/UC-XX/stages/NN_*/CONTEXT.md` | What the agent does in that stage |
| **API schema** | `reference-impl/.../api/*.yaml` (or equivalent) | The shape of an HTTP/RPC surface |

## What is *not* a contract

- A chat message ("can you also do X?")
- An undocumented inline edit to generated code
- An informal email or issue comment that was not lifted into a file

If something authorising a change exists only in conversation, it is not
a contract — and the change it authorises is not legitimate under CLAD.
**Lift it into a file first.**

## Contract qualities

Every contract should be:

1. **Small.** A use case is a paragraph and a list of scenarios, not a
   30-page spec. A concept is one screen of markdown.
2. **Reviewable in isolation.** A reviewer should not need to read three
   other contracts to understand whether this one is correct.
3. **Versioned.** Contracts live in git. Their evolution is the audit
   trail of the system.
4. **Stable on the relevant time scale.** A use case may live for the
   life of the feature. A concept spec may change with each refactor.
   A stage `CONTEXT.md` may change as you tune the workflow.

## Contract lifecycle

```
  draft  ->  human-edited  ->  approved  ->  implemented  ->  verified
                                  ^                                |
                                  +-- changed by back-trace -------+
```

Contracts are never frozen. A failure surfaced in stage 5 (verification)
is allowed — and expected — to send you back to amend the use case or a
concept spec.
