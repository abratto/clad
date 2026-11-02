## Machine model

```
object-type Client identified-by ClientId
object-type Firm identified-by FirmUri
object-type Service identified-by Service
fact firmByClientId : ClientId -> FirmUri -- mandatory
fact provides : FirmUri -> { Service } -- zero or more
fact serviceName : Service -> ServiceName -- mandatory
fact serviceJurisdiction : ( FirmUri, Service ) -> Jurisdiction -- optional
fact capabilityStatus : ( FirmUri, Service ) -> Status -- optional
```
