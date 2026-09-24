-- Base DDL for the login concept state (UC-00-login).
--
-- Derived from the Stage 03b conceptual data models via Halpin's R-map —
-- the same derivation `dev.legible.storage.LoginSchemas` performs at runtime
-- (`RelationSchema.ddl()`, executed idempotently by
-- `RmapPostgresFactStore.createSchema()` at startup). This Flyway migration
-- mirrors those statements so the migration timeline documents the base and
-- jOOQ codegen can introspect it.
--
-- Mirror fidelity note: mandatory roles are NOT emitted as NOT NULL — the
-- Region SPI writes facts one at a time, so a row-level constraint would
-- reject the first of several writes. Typed columns, DEFAULT for resettable
-- facts, and UNIQUE constraints are enforced by the database, exactly as the
-- runtime R-map DDL does (varchar stands in for TEXT for the jOOQ DDLDatabase
-- parser; semantics are identical on Postgres).

CREATE TABLE IF NOT EXISTS "user_naming" (
    "user_id"    varchar(40) PRIMARY KEY,
    "username"   varchar(255) UNIQUE
);

CREATE TABLE IF NOT EXISTS "password_auth" (
    "user_id"         varchar(40) PRIMARY KEY,
    "password_hash"   varchar(255),
    "failed_attempts" integer DEFAULT 0,
    "locked_until"    timestamp
);

CREATE TABLE IF NOT EXISTS "session" (
    "session_id" varchar(40) PRIMARY KEY,
    "user_id"    varchar(40),
    "opened_at"  timestamp
);
