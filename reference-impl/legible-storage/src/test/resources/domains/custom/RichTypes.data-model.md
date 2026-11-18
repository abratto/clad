## Conceptual model

```
object-type Entity identified-by Entity
fact amount : Entity -> Decimal(12,2) -- mandatory
fact externalId : Entity -> UUID -- mandatory
fact bornOn : Entity -> Date -- optional
fact opensAt : Entity -> Time -- optional
fact metadata : Entity -> JSONB -- optional
fact payload : Entity -> Bytes -- optional
```

## Notes

- Exercises the built-in scalar type map: numeric with precision/scale, UUID,
  date, time, JSONB, and bytea (base64 at the SPI boundary).
