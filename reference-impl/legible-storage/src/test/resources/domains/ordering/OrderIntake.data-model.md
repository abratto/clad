# OrderIntake — conceptual data model

## Step 2 — Draft fact model and population check

### Object types

- Entity: `Order`
- Entity: `Product`

### Fact types

- `orderNumber: Order -> OrderNumber` (unique)
- `totalCents: Order -> Int` (mandatory, default 0)
- `status: Order -> Status` (mandatory, enum)
- `placedAt: Order -> Timestamp` (mandatory)
- `tags: Order -> { Tag }` (multi-valued)
- `line: (Order, Product) -> Int` (mandatory)

### Population check

- An order carries its number, running total, status, placement time, any
  number of tags, and one quantity per ordered product.

## Machine model

```
object-type Order identified-by Order
object-type Product identified-by Product
fact orderNumber : Order -> OrderNumber -- mandatory, unique
fact totalCents : Order -> Int -- mandatory, default 0
fact status : Order -> Status -- mandatory, in {open, paid, shipped}
fact placedAt : Order -> Timestamp -- mandatory
fact tags : Order -> { Tag } -- zero or more
fact line : ( Order, Product ) -> Int -- mandatory
```

## Modeling Notes

- Line items are an objectified (Order, Product) pair carrying the quantity.
- `tags` is a multi-valued fact realised as its own child table.
