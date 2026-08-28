package dev.legible.storage;

import java.util.List;

/**
 * Rmap-derived relational schemas for the UC-00-login concepts, from their
 * Stage 03b conceptual data models:
 *
 * <ul>
 *   <li>{@code UserNaming} — {@code username: UserId -> String} (mandatory,
 *       unique) → table {@code usernaming(user_id PK, username UNIQUE)}.</li>
 *   <li>{@code PasswordAuth} — {@code passwordHash / failedAttempts /
 *       lockedUntil} over {@code UserId} → table
 *       {@code passwordauth(user_id PK, password_hash, failed_attempts,
 *       locked_until)}.</li>
 *   <li>{@code Session} — {@code userId / openedAt} over {@code SessionId} →
 *       table {@code session(session_id PK, user_id, opened_at)}.</li>
 * </ul>
 *
 * <p>Columns are {@code TEXT} because the engine's {@code Region} SPI is
 * string-valued; a fully typed profile would map {@code Int} and
 * {@code Timestamp} fact types to {@code INTEGER}/{@code TIMESTAMP} columns at
 * the same Stage 04a mapping.
 */
public final class LoginSchemas {

    private LoginSchemas() {
    }

    public static List<RelationSchema> all() {
        return List.of(
                new RelationSchema("UserNaming", "usernaming", "user_id",
                        List.of(new RelationSchema.Column("username", "username", "TEXT", true))),
                new RelationSchema("PasswordAuth", "passwordauth", "user_id",
                        List.of(
                                new RelationSchema.Column("passwordHash", "password_hash", "TEXT", false),
                                new RelationSchema.Column("failedAttempts", "failed_attempts", "TEXT", false),
                                new RelationSchema.Column("lockedUntil", "locked_until", "TEXT", false))),
                new RelationSchema("Session", "session", "session_id",
                        List.of(
                                new RelationSchema.Column("userId", "user_id", "TEXT", false),
                                new RelationSchema.Column("openedAt", "opened_at", "TEXT", false))));
    }
}
