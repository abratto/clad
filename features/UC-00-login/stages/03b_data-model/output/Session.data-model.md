# Session — conceptual data model

## Step 1 — Familiar examples and elementary facts

### Familiar examples

- Session `s1` belongs to user `u1`.
- Session `s1` was opened at timestamp `t1`.

### Elementary facts

- Session `s1` belongs to UserId `u1`.
- Session `s1` has OpenedAtTimestamp `t1`.

### Step 1 quality checks

- `SessionId` is the identifier for `Session`.
- `UserId` remains an opaque value and is not modeled as a foreign key.

## Step 2 — Draft fact model and population check

### Object types

- Entity: `Session`
- Values: `SessionId`, `UserId`, `Timestamp`

### Fact types

- `Session` is identified by `SessionId`.
- `Session` belongs to `UserId`.
- `Session` has `OpenedAtTimestamp`.

### Population check

- The familiar examples populate all three fact types.

## Step 3 — Combination and arithmetic derivation checks

### Entity-type combination check

- None.

### Arithmetic derivations

- None.

## Step 4 — Uniqueness constraints and arity checks

### Uniqueness constraints

- Each `SessionId` identifies at most one `Session`.
- Each `Session` has at most one `UserId`.
- Each `Session` has at most one `OpenedAtTimestamp`.

### Arity checks

- All fact types are binary.
- No hidden functional dependency requires splitting or recombination.

## Step 5 — Mandatory roles and logical derivations

### Mandatory role constraints

- Every `Session` has exactly one `UserId`.
- Every `Session` has exactly one `OpenedAtTimestamp`.

### Logical derivations

- None.

## Step 6 — Value, set comparison, and subtype constraints

### Value constraints

- None beyond `Timestamp` belonging to its timestamp domain.

### Set comparison constraints

- None.

### Subtype constraints

- None.

## Step 7 — Other constraints and final checks

### Other constraints

- None.

### Final checks

- The model matches the approved `Session` state section.
- No Pattern D exposure exists for `Session` in UC-00.
- No cross-concept schema relationship to `User` is introduced.

## Modeling Notes

- `UserId` remains an opaque value; this stage does not model a cross-concept foreign-key relationship to `User`.