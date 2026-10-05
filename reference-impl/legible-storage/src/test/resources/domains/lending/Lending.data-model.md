# Lending — conceptual data model

## Step 2 — Draft fact model and population check

### Object types

- Entity: `Copy`
- Entity: `Loan`
- Entity: `Member`

### Fact types

- `copyCode: Copy -> CopyCode` (unique)
- `title: Copy -> Title`
- `borrower: Loan -> Member`
- `openedAt: Loan -> Timestamp`
- `loanCopy: Loan -> Copy` (mandatory, unique)
- `returnedAt: Loan -> Timestamp` (optional)

### Population check

- A loan is opened by a member for a copy and may later be returned.

## Machine model

```
object-type Copy identified-by Copy
object-type Loan identified-by Loan
object-type Member identified-by Member
fact copyCode : Copy -> CopyCode -- mandatory, unique
fact title : Copy -> Title -- mandatory
fact borrower : Loan -> Member -- mandatory
fact openedAt : Loan -> Timestamp -- mandatory
fact loanCopy : Loan -> Copy -- mandatory, unique
fact returnedAt : Loan -> Timestamp -- optional
```

## Modeling Notes

- A loan is identified by the (member, copy) pair, not by an own id; the
  referenced copy column carries `unique`, i.e. at most one loan row mentions
  a given copy at all — the probe target for loan history.
