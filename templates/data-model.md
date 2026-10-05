<!-- Template for Stage 03b (03b_data-model). Purpose: see methodology/architecture/DATA_MODEL_NOTES.md. -->

# <Concept> — conceptual data model

## Step 1 — Familiar examples and elementary facts

### Familiar examples

- <example sentence from the approved state section>
- <example sentence from the approved state section>

### Elementary facts

- <elementary fact 1>
- <elementary fact 2>

### Step 1 quality checks

- <object identification check>
- <split/recombine check>

## Step 2 — Draft fact model and population check

### Object types

- Entity: `<EntityType>`
- Value: `<ValueType>`

### Fact types

- `<FactType>`
- `<FactType>`

### Population check

- <sample population row or statement that at least one example populates each fact type>

## Step 3 — Combination and arithmetic derivation checks

### Entity-type combination check

- <combined entity types, or `None`>

### Arithmetic derivations

- <derivable quantity/count, or `None`>

## Step 4 — Uniqueness constraints and arity checks

### Uniqueness constraints

- <uniqueness constraint>
- <uniqueness constraint>

### Arity checks

- <arity check result>

## Step 5 — Mandatory roles and logical derivations

### Mandatory role constraints

- <mandatory role constraint>
- <mandatory role constraint>

### Logical derivations

- <logical derivation rule, or `None`>

## Step 6 — Value, set comparison, and subtype constraints

### Value constraints

- <value constraint, or `None`>

### Set comparison constraints

- <subset/equality/exclusion constraint, or `None`>

### Subtype constraints

- <subtype constraint, or `None`>

## Step 7 — Other constraints and final checks

### Other constraints

- <other constraint, or `None`>

### Final checks

- <consistency/completeness check>
- <redundancy or optimization note>

## Machine model

<!-- CSDP-aligned fact/constraint block consumed by Rmap. Generated
     deterministically from the concept `## State`; keep it a faithful
     transcription of Steps 2/4/5. See DATA_MODEL_NOTES.md §"The machine model
     block". Do not put SQL/storage constructs here. -->

```
object-type <EntityType> identified-by <IdType>
fact <predicate> : <EntityType> -> <ValueType> -- <mandatory|optional[, unique][, default X]> 
fact <predicate> : ( <A>, <B> ) -> <ValueType> -- <annotations>
fact <predicate> : <EntityType> -> { <ValueType> } -- <annotations>
<Sub> is a <Sup> -- mapping: absorb | separate | partition
independent <ObjectType>
```

## Modeling Notes

- <non-obvious modeling decision, or `No notable decisions.`>