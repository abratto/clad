# PasswordAuth — conceptual data model

## Step 1 — Familiar examples and elementary facts

### Familiar examples

- PasswordAuth record for user `u1` has password hash `h1`.
- PasswordAuth record for user `u1` has failed-attempt count `0`.
- PasswordAuth record for user `u1` may have locked-until timestamp `t1`.

### Elementary facts

- PasswordAuthRecord for UserId `u1` has PasswordHash `h1`.
- PasswordAuthRecord for UserId `u1` has failed-attempt Count `0`.
- PasswordAuthRecord for UserId `u1` has LockedUntilTimestamp `t1`.

### Step 1 quality checks

- `UserId` is treated as an opaque reference value, not as a cross-concept foreign key.
- The lock timestamp remains optional, so its fact stays separate rather than being folded into the mandatory facts.

## Step 2 — Draft fact model and population check

### Object types

- Entity: `PasswordAuthRecord`
- Values: `UserId`, `PasswordHash`, `Int`, `Timestamp`

### Fact types

- `PasswordAuthRecord` is identified by `UserId`.
- `PasswordAuthRecord` has `PasswordHash`.
- `PasswordAuthRecord` has failed-attempt `Count`.
- `PasswordAuthRecord` has `LockedUntilTimestamp`.

### Population check

- The familiar examples populate the identifier, password-hash, and failed-attempt facts.
- The lock-timestamp fact is populated only for locked records and remains optional.

## Step 3 — Combination and arithmetic derivation checks

### Entity-type combination check

- No separate `Credential` and `Lock` entity types are introduced; they combine into one `PasswordAuthRecord` conceptual entity keyed by `UserId`.

### Arithmetic derivations

- None.

## Step 4 — Uniqueness constraints and arity checks

### Uniqueness constraints

- Each `UserId` identifies at most one `PasswordAuthRecord`.
- Each `PasswordAuthRecord` has at most one `PasswordHash`.
- Each `PasswordAuthRecord` has at most one failed-attempt `Count`.
- Each `PasswordAuthRecord` has at most one `LockedUntilTimestamp`.

### Arity checks

- All fact types are binary after keeping the identifier as a separate fact.
- No hidden functional dependency requires splitting a wider fact type.

## Step 5 — Mandatory roles and logical derivations

### Mandatory role constraints

- Every credentialed `PasswordAuthRecord` has exactly one `PasswordHash`.
- Every `PasswordAuthRecord` has exactly one failed-attempt `Count`.
- `LockedUntilTimestamp` is optional.

### Logical derivations

- Locked/not-locked status is logically derived from whether `LockedUntilTimestamp` exists and lies in the future.

## Step 6 — Value, set comparison, and subtype constraints

### Value constraints

- Failed-attempt `Count` is a non-negative integer domain.

### Set comparison constraints

- None.

### Subtype constraints

- None.

## Step 7 — Other constraints and final checks

### Other constraints

- Failed-attempt `Count` conceptually defaults to zero when the record is established.

### Final checks

- The model matches the approved `PasswordAuth` state section.
- No Pattern D exposure exists for `PasswordAuth` in UC-00.
- No cross-concept schema relationship to `User` is introduced.

## Modeling Notes

- `UserId` is an opaque identifier owned elsewhere; no cross-concept foreign-key relationship is modeled here.