# Relational lowering — Stage 03b data model → Postgres schema

The deterministic contract for mapping an approved Stage 03b conceptual data
model into this profile's relational schema. This is the relational analog of
`SYNC_LOWERING.md` (which does the same job for syncs → SPARQL).

## Source of truth

Stage 03b produces a profile-neutral CSDP fact model (Halpin's ORM tradition —
see `methodology/architecture/DATA_MODEL_NOTES.md`). Its relational mapping is
Halpin's **Rmap**: a fact type becomes either an absorbed column or a separate
table, decided by **arity**, the **uniqueness constraint**, and **mandatory
roles**. CLAD adds one constraint of its own: **no cross-concept foreign key**.

## The mapping rules

| Stage 03b form | Relational realization |
|---|---|
| `field: S -> V` (mandatory) | column on S's table, `NOT NULL` |
| `field: S -> V` (optional) | column on S's table, nullable |
| `field: S -> V` with a default | column with a `DEFAULT` |
| `List<T>` / `Map<K,V>` / "zero or more" | child table, composite PK, intra-concept FK to S's table |
| nested struct / objectified fact | separate table, surrogate or composite key |
| value constraint (e.g. enum) | `CHECK` constraint |
| uniqueness constraint | `UNIQUE` (or `PRIMARY KEY` on the subject column) |
| intra-concept entity reference | real FK (same concept) |
| **cross-concept identifier** | **opaque typed column — never a FK** |

### Worked example — the three UC-00-login concepts

```
User:        username: UserId -> String            (mandatory, unique)
PasswordAuth: passwordHash: UserId -> PasswordHash  (mandatory)
              failedAttempts: UserId -> Int         (mandatory, default 0)
              lockedUntil: UserId -> Timestamp      (optional)
Session:     token -> UserId                        (via grant)
```

```sql
CREATE TABLE "user_accounts" (
    "user_id"   uuid PRIMARY KEY,
    "username"  varchar(255) NOT NULL UNIQUE
);
CREATE TABLE "passwordauth_credentials" (
    "user_id"         uuid PRIMARY KEY,     -- opaque; NO FK to user_accounts
    "password_hash"   text NOT NULL,
    "failed_attempts" int  NOT NULL DEFAULT 0,
    "locked_until"    timestamptz NULL
);
CREATE TABLE "session_tokens" (
    "session_token" uuid PRIMARY KEY,
    "user_id"       uuid NOT NULL           -- opaque; NO FK
);
```

`user_id` appears in three concepts' tables as an opaque value. No foreign key
crosses a concept boundary — that is R2 ("one storage region per concept, no
cross-region reads") expressed at the DDL level.

## Schema-per-application + concept-prefix ownership

One application schema (default `public`); every table's name carries its owning
concept as a prefix (`user_accounts`, `passwordauth_credentials`,
`session_tokens`). The prefix is the concept's lowercase name, so the owner of a
table is always legible and mechanically checkable.

## Constraint realization

- **Uniqueness** → `UNIQUE` / `PRIMARY KEY`.
- **Mandatory** → `NOT NULL`.
- **Optional** → nullable column.
- **Value constraints** → `CHECK`.
- **Set/subset** → FK (intra-concept only).

## Traceability

The mapping must stay traceable to the approved Stage 03b elementary facts —
Stage 04a must not invent new facts, fields, or constraints. If a fact type
cannot be mapped without inventing structure, repair the conceptual model first,
exactly as `methodology/implementation/STORAGE_MAPPING.md` requires.
