# Flow — <name>

> A flow is a named, expected chain of concept actions for a particular
> scenario. It is the prediction that stage 5 verifies against the
> actual flow-token tree.

## Triggered by

- `Web.handle <method> <route>` from scenario "<name>" in
  `../01_usecase/output/usecase.md`

## Expected chain

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
