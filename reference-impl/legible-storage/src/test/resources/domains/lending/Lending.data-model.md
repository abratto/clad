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
- `loanCopy: Loan -> Copy` (mandatory, unique while returnedAt absent)
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
fact loanCopy : Loan -> Copy -- mandatory, unique while returnedAt absent
fact returnedAt : Loan -> Timestamp -- optional
```

## Modeling Notes

- A loan is identified by its own `Loan` id; `loanCopy` is unique **while
  `returnedAt` is absent** — at most one open loan per copy, loan history
  preserved once a loan is returned (filtered uniqueness).
