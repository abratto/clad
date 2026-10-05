# PatientRegistry — conceptual data model

## Step 2 — Draft fact model and population check

### Object types

- Entity: `Person`
- Entity: `Patient`
- Value: `Timestamp`
- Value: `Gender`
- Value: `InsurerName`

### Fact types

- `registeredAt: Person -> Timestamp`
- `gender: Person -> Gender`
- `insurerName: Patient -> InsurerName`

### Population check

- Every person registers and has a gender; only patients carry an insurer.

## Machine model

```
object-type Person identified-by Person
object-type Patient identified-by Patient
fact registeredAt : Person -> Timestamp -- mandatory
fact gender : Person -> Gender -- mandatory, in {M, F}
fact insurerName : Patient -> InsurerName -- optional
Patient is a Person -- mapping: separate
```

## Modeling Notes

- `Patient` is separated from `Person`: patient-specific facts live in their
  own table keyed on the supertype's identity column.
