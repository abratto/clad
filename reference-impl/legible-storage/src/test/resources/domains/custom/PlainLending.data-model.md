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
