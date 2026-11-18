## Conceptual model

```
object-type User identified-by User
fact tenant : User -> Tenant -- mandatory
fact email : User -> Email -- mandatory
fact deletedAt : User -> Timestamp -- optional
unique ( tenant, email ) while deletedAt absent
```

## Notes

- The email is unique within a tenant while the row is open; a soft-deleted
  row frees the pair for reuse.
