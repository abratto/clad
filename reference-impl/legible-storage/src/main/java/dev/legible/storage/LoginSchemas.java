package dev.legible.storage;

import java.util.List;

/**
 * The UC-00-login relational schemas, <em>derived</em> from the Stage 02
 * concept specs' {@code ## State} notation by {@link RmapDeriver} — not
 * hand-authored. The state notation below is copied verbatim from
 * {@code features/UC-00-login/stages/02_concepts/output/*.concept.md};
 * {@link RmapDeriverTest} re-reads those files and asserts the derivation
 * matches, so the schema cannot drift from the spec.
 */
public final class LoginSchemas {

    private LoginSchemas() {
    }

    // Verbatim `## State` blocks from the Stage 02 concept specs.
    private static final String USER_NAMING_STATE = """
            username: UserId -> String   -- mandatory, unique across all users
            """;

    private static final String PASSWORD_AUTH_STATE = """
            passwordHash: UserId -> PasswordHash     -- mandatory
            failedAttempts: UserId -> Int            -- mandatory, default 0
            lockedUntil: UserId -> Timestamp         -- optional
            """;

    private static final String SESSION_STATE = """
            userId: SessionId -> UserId       -- mandatory
            openedAt: SessionId -> Timestamp  -- mandatory
            """;

    public static List<RelationSchema> all() {
        return List.of(
                RmapDeriver.derive("UserNaming", USER_NAMING_STATE),
                RmapDeriver.derive("PasswordAuth", PASSWORD_AUTH_STATE),
                RmapDeriver.derive("Session", SESSION_STATE));
    }
}
