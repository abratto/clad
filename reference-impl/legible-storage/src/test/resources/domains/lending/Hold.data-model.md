# Hold — conceptual data model

## Step 2 — Draft fact model and population check

### Object types

- Entity: `Member`
- Entity: `Copy`

### Fact types

- `hold: (Member, Copy) -> Priority` (optional)

### Population check

- A member may place a hold on a copy with an optional priority.

## Machine model

```
object-type Member identified-by Member
object-type Copy identified-by Copy
fact hold : ( Member, Copy ) -> Priority -- optional
```

## Modeling Notes

- The hold individual exists per (member, copy) pair; the priority is optional,
  so the keyed row may carry no priority value at all.
