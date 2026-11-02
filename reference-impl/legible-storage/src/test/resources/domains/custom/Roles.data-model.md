## Machine model

```
object-type Party identified-by Party
object-type Client identified-by Client
object-type Supplier identified-by Supplier
fact partyName : Party -> PartyName -- mandatory
fact discountRate : Client -> Int -- optional
fact creditLimit : Supplier -> Int -- optional
Client is a Party -- mapping: partition
Supplier is a Party -- mapping: partition
```
