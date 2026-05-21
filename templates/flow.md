<!-- Flow prediction template. Purpose: see methodology/architecture/FLOW_TOKENS.md. -->

# Flow — <name>

> A flow is a named, expected chain of concept actions for a particular
> scenario. It is the prediction that stage 5 verifies against the
> actual flow-token tree.

## Triggered by

- `Web.handle <method> <route>` from scenario "<name>" in
  `../01_usecase/output/usecase.md`

## Expected chain

This section is the **expected authored action chain**. It is not just a
token count prediction; it names the concept actions that must exist at
runtime for this scenario to be considered correctly implemented.

```
Web.handle(<route>)
  └─ <Concept>.<action>(<args>)
       └─ <Concept>.<action>(<args>)
       └─ <Concept>.<action>(<args>)
```

## Authorising syncs

- `../03_syncs/output/<name>.sync.md`
- `../03_syncs/output/<name>.sync.md`

## Notes

> Optional.

> If a scenario can reach the correct final HTTP response without
> producing this authored action chain, the implementation is wrong even
> if the response matches.
