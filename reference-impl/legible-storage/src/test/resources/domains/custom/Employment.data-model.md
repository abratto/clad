## Machine model

```
object-type Party identified-by Party
object-type Employer identified-by Employer
fact partyName : Party -> PartyName -- mandatory
fact vatNumber : Employer -> VatNumber -- mandatory
Employer is a Party -- mapping: absorb
```
