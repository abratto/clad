package dev.legible.bench.concurrency;

import dev.legible.storage.RelationSchema;

import java.util.List;

/** Minimal R-map schemas for the throwaway concurrency lab (Counter + Account). */
public final class ConcurrencyLabSchemas {

    private ConcurrencyLabSchemas() {
    }

    public static List<RelationSchema> all() {
        return List.of(counter(), account());
    }

    private static RelationSchema counter() {
        return new RelationSchema(
                "Counter", "counter", "CounterId",
                List.of(
                        new RelationSchema.Column("counter_id", "counter_id", "TEXT",
                                true, false, null),
                        new RelationSchema.Column("count", "count", "INTEGER",
                                true, false, "0")),
                List.of("counter_id"), List.of(), List.of(), false,
                "CREATE TABLE IF NOT EXISTS counter ("
                        + "counter_id TEXT PRIMARY KEY, "
                        + "count INTEGER NOT NULL DEFAULT 0)");
    }

    private static RelationSchema account() {
        return new RelationSchema(
                "Account", "account", "AccountId",
                List.of(
                        new RelationSchema.Column("account_id", "account_id", "TEXT",
                                true, false, null),
                        new RelationSchema.Column("balance", "balance", "INTEGER",
                                true, false, "0")),
                List.of("account_id"), List.of(), List.of(), false,
                "CREATE TABLE IF NOT EXISTS account ("
                        + "account_id TEXT PRIMARY KEY, "
                        + "balance INTEGER NOT NULL DEFAULT 0)");
    }
}
