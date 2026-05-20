# User — conceptual data model

## Step 1 — Familiar examples and elementary facts

### Familiar examples

- User `u1` has username `alice`.
- Username `alice` identifies user `u1`.

### Elementary facts

- User `u1` has Username `alice`.
- User `u1` is identified by UserId `u1`.

### Step 1 quality checks

- `User` is identified by opaque `UserId`; `Username` alone is not used as the global identifier.
- No sentence needed splitting beyond these elementary facts.

## Step 2 — Draft fact model and population check

### Object types

- Entity: `User`
- Values: `UserId`, `Username`

### Fact types

- `User` is identified by `UserId`.
- `User` has `Username`.

### Population check

- The familiar examples populate both fact types.

## Step 3 — Combination and arithmetic derivation checks

### Entity-type combination check

- None.

### Arithmetic derivations

- None.

## Step 4 — Uniqueness constraints and arity checks

### Uniqueness constraints

- Each `UserId` identifies at most one `User`.
- Each `Username` identifies at most one `User`.

### Arity checks

- Both fact types remain binary; no hidden dependency requires further splitting.

## Step 5 — Mandatory roles and logical derivations

### Mandatory role constraints

- Every `User` has exactly one `Username`.
- Every `User` has exactly one `UserId`.

### Logical derivations

- None.

## Step 6 — Value, set comparison, and subtype constraints

### Value constraints

- None beyond `Username` being a string-valued domain.

### Set comparison constraints

- None.

### Subtype constraints

- None.

## Step 7 — Other constraints and final checks

### Other constraints

- None.

### Final checks

- The model matches the approved `User` state section exactly.
- No Pattern D exposure exists for `User` in UC-00.
- No cross-concept coupling is introduced.

## Modeling Notes

- No notable decisions — straight CSDP walk from the approved state section.