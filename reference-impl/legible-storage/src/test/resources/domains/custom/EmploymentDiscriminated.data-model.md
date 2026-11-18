## Conceptual model

```
object-type Party identified-by Party
object-type Employer identified-by Employer
fact partyName : Party -> Name -- mandatory
fact partyKind : Party -> PartyKind -- mandatory, in {individual, employer}
fact vatNumber : Employer -> VatNumber -- mandatory
Employer is a Party -- mapping: absorb, discriminator partyKind = employer
```

## Notes

- `partyKind` is the explicit membership discriminator. An employer must have
  a VAT number; an individual must not have one.
