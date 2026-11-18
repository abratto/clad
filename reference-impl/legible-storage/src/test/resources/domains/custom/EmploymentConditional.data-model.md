## Conceptual model

```
object-type Party identified-by Party
object-type Employer identified-by Employer
fact partyName : Party -> PartyName -- mandatory
fact vatNumber : Employer -> VatNumber -- mandatory
fact payrollRef : Employer -> PayrollRef -- optional
Employer is a Party -- mapping: absorb
```

## Notes

- `Employer` is absorbed: its facts are nullable on the `Party` table and a
  membership check allows a non-employer (both null) or an employer (VAT
  present). A payroll reference without a VAT number is invalid.
