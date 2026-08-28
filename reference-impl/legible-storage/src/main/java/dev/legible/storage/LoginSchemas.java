package dev.legible.storage;

import java.util.List;

/**
 * Rmap-derived relational schemas for the UC-00-login concepts, from their
 * Stage 03b conceptual data models:
 *
 * <ul>
 *   <li>{@code UserNaming} — {@code username: UserId -> String} (mandatory,
 *       unique) → {@code usernaming(user_id PK, username TEXT NOT NULL
 *       UNIQUE)}.</li>
 *   <li>{@code PasswordAuth} — {@code passwordHash} (mandatory),
 *       {@code failedAttempts: Int} (mandatory, default 0),
 *       {@code lockedUntil: Timestamp} (optional) →
 *       {@code passwordauth(user_id PK, password_hash TEXT NOT NULL,
 *       failed_attempts INTEGER NOT NULL DEFAULT 0, locked_until
 *       TIMESTAMP)}.</li>
 *   <li>{@code Session} — {@code userId} (mandatory), {@code openedAt:
 *       Timestamp} (mandatory) → {@code session(session_id PK, user_id TEXT
 *       NOT NULL, opened_at TIMESTAMP NOT NULL)}.</li>
 * </ul>
 *
 * <p>Value types round-trip through the string-valued {@code Region} SPI:
 * {@code Int} facts store as {@code INTEGER} columns (decimal-string), and
 * {@code Timestamp} facts store as {@code TIMESTAMP} columns (epoch-millisecond
 * strings).
 */
public final class LoginSchemas {

    private LoginSchemas() {
    }

    public static List<RelationSchema> all() {
        return List.of(
                new RelationSchema("UserNaming", "usernaming", "user_id",
                        List.of(new RelationSchema.Column(
                                "username", "username", "TEXT", true, true, null))),
                new RelationSchema("PasswordAuth", "passwordauth", "user_id",
                        List.of(
                                new RelationSchema.Column(
                                        "passwordHash", "password_hash", "TEXT", true, false, null),
                                new RelationSchema.Column(
                                        "failedAttempts", "failed_attempts", "INTEGER", true, false, "0"),
                                new RelationSchema.Column(
                                        "lockedUntil", "locked_until", "TIMESTAMP", false, false, null))),
                new RelationSchema("Session", "session", "session_id",
                        List.of(
                                new RelationSchema.Column(
                                        "userId", "user_id", "TEXT", true, false, null),
                                new RelationSchema.Column(
                                        "openedAt", "opened_at", "TIMESTAMP", true, false, null))));
    }
}
