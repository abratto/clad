package com.example.app.concepts.passwordauth;

import dev.clad.engine.ActionLog;
import dev.clad.engine.ActionRecord;
import dev.clad.engine.CompletionBus;
import dev.clad.engine.ConceptAgent;
import dev.clad.engine.SyncEvaluator;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;
import org.apache.jena.rdf.model.ResourceFactory;
import org.jooq.DSLContext;

import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.Map;
import java.util.UUID;

import static com.example.app.db.tables.PasswordauthCredentials.PASSWORDAUTH_CREDENTIALS;

/**
 * The PasswordAuth concept: stores a password verifier per userId and checks
 * supplied passwords. State lives in the {@code passwordauth_credentials} table.
 *
 * <p>Verifier is a plain hash placeholder for the reference profile — replace
 * with a real KDF (Argon2/bcrypt) in production profiles.
 *
 * <p>Actions:
 * <ul>
 *   <li>{@code setCredential} — input: {@code userId, password}.</li>
 *   <li>{@code check} — input: {@code userId, password}; output: {@code outcome}
 *       in {@code OK | BAD_PASSWORD | NO_CREDENTIAL | LOCKED}.</li>
 * </ul>
 */
@Singleton
public final class PasswordAuthConcept extends ConceptAgent {

    public static final String IRI = "https://clad.dev/concept/passwordauth";

    private static final int LOCKOUT_THRESHOLD = 5;
    private static final long LOCKOUT_WINDOW_MILLIS = 15L * 60L * 1000L;

    private final DSLContext dsl;

    @Inject
    public PasswordAuthConcept(ActionLog actionLog, CompletionBus completionBus,
                               SyncEvaluator evaluator, DSLContext dsl) {
        super(actionLog, completionBus, evaluator);
        this.dsl = dsl;
    }

    /** Test-only constructor — sync evaluation bypassed for isolated tests. */
    public PasswordAuthConcept(ActionLog actionLog, CompletionBus completionBus, DSLContext dsl) {
        super(actionLog, completionBus);
        this.dsl = dsl;
    }

    @Override
    protected String conceptIRI() {
        return IRI;
    }

    @Override
    public void pollAll() {
        pollAndProcess("setCredential");
        pollAndProcess("check");
    }

    @Override
    protected void processInvocation(ActionRecord invocation) {
        switch (invocation.actionName()) {
            case "setCredential" -> doSet(invocation);
            case "check" -> doCheck(invocation);
            default -> writeError(invocation, "unknown action: " + invocation.actionName());
        }
    }

    /** Test/seed helper. */
    public void seedCredential(String userId, String password) {
        upsert(userId, verify(password), 0, null);
    }

    private void upsert(String userId, String verifier, int failedAttempts, Long lockedUntilMillis) {
        OffsetDateTime lockedUntil = lockedUntilMillis == null ? null
                : OffsetDateTime.ofInstant(Instant.ofEpochMilli(lockedUntilMillis), ZoneOffset.UTC);
        dsl.insertInto(PASSWORDAUTH_CREDENTIALS,
                        PASSWORDAUTH_CREDENTIALS.USER_ID, PASSWORDAUTH_CREDENTIALS.PASSWORD_HASH,
                        PASSWORDAUTH_CREDENTIALS.FAILED_ATTEMPTS, PASSWORDAUTH_CREDENTIALS.LOCKED_UNTIL)
                .values(UUID.fromString(userId), verifier, failedAttempts, lockedUntil)
                .onConflict(PASSWORDAUTH_CREDENTIALS.USER_ID)
                .doUpdate()
                .set(PASSWORDAUTH_CREDENTIALS.PASSWORD_HASH, verifier)
                .set(PASSWORDAUTH_CREDENTIALS.FAILED_ATTEMPTS, failedAttempts)
                .set(PASSWORDAUTH_CREDENTIALS.LOCKED_UNTIL, lockedUntil)
                .execute();
    }

    private void doSet(ActionRecord invocation) {
        String userId = invocation.binding("userId");
        String password = invocation.binding("password");
        if (userId == null || password == null) {
            writeError(invocation, "missing userId or password");
            return;
        }
        seedCredential(userId, password);
        writeCompletion(invocation, Map.of(
                "outcome", ResourceFactory.createStringLiteral("SET"),
                "userId", ResourceFactory.createStringLiteral(userId)));
    }

    private void doCheck(ActionRecord invocation) {
        String userId = invocation.binding("userId");
        String password = invocation.binding("password");
        if (userId == null || password == null) {
            writeError(invocation, "missing userId or password");
            return;
        }
        String outcome;
        AuthState state = lookupAuthState(userId);
        long now = System.currentTimeMillis();
        if (state == null) {
            outcome = "NO_CREDENTIAL";
        } else if (state.lockedUntilMillis() != null && state.lockedUntilMillis() > now) {
            outcome = "LOCKED";
        } else if (state.verifier().equals(verify(password))) {
            upsert(userId, state.verifier(), 0, null);
            outcome = "OK";
        } else {
            int failedAttempts = state.failedAttempts() + 1;
            Long lockedUntilMillis = failedAttempts >= LOCKOUT_THRESHOLD
                    ? now + LOCKOUT_WINDOW_MILLIS
                    : null;
            upsert(userId, state.verifier(), failedAttempts, lockedUntilMillis);
            outcome = "BAD_PASSWORD";
        }
        writeCompletion(invocation, Map.of(
                "outcome", ResourceFactory.createStringLiteral(outcome),
                "userId", ResourceFactory.createStringLiteral(userId)));
    }

    private AuthState lookupAuthState(String userId) {
        var record = dsl.select(
                        PASSWORDAUTH_CREDENTIALS.PASSWORD_HASH,
                        PASSWORDAUTH_CREDENTIALS.FAILED_ATTEMPTS,
                        PASSWORDAUTH_CREDENTIALS.LOCKED_UNTIL)
                .from(PASSWORDAUTH_CREDENTIALS)
                .where(PASSWORDAUTH_CREDENTIALS.USER_ID.eq(UUID.fromString(userId)))
                .fetchOne();
        if (record == null) {
            return null;
        }
        Integer attempts = record.get(PASSWORDAUTH_CREDENTIALS.FAILED_ATTEMPTS);
        OffsetDateTime lockedUntil = record.get(PASSWORDAUTH_CREDENTIALS.LOCKED_UNTIL);
        return new AuthState(
                record.get(PASSWORDAUTH_CREDENTIALS.PASSWORD_HASH),
                attempts == null ? 0 : attempts,
                lockedUntil == null ? null : lockedUntil.toInstant().toEpochMilli());
    }

    private record AuthState(String verifier, int failedAttempts, Long lockedUntilMillis) {}

    /** Trivial verifier — DO NOT USE IN PRODUCTION. */
    private static String verify(String password) {
        return "sha256:" + Integer.toHexString(password.hashCode());
    }
}
