package com.example.app.concepts.session;

import dev.clad.engine.ActionLog;
import dev.clad.engine.ActionRecord;
import dev.clad.engine.CompletionBus;
import dev.clad.engine.ConceptAgent;
import dev.clad.engine.SyncEvaluator;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;
import org.apache.jena.rdf.model.ResourceFactory;
import org.jooq.DSLContext;

import java.util.Map;
import java.util.UUID;

import static com.example.app.db.tables.SessionTokens.SESSION_TOKENS;

/**
 * The Session concept: mints opaque session tokens for authenticated users.
 * State lives in the {@code session_tokens} table.
 *
 * <p>Actions:
 * <ul>
 *   <li>{@code grant} — input: {@code userId}; output:
 *       {@code outcome=GRANTED, sessionId=<uuid>}.</li>
 *   <li>{@code lookup} — input: {@code sessionId}; output:
 *       {@code outcome=ACTIVE|UNKNOWN, userId=...}.</li>
 * </ul>
 */
@Singleton
public final class SessionConcept extends ConceptAgent {

    public static final String IRI = "https://clad.dev/concept/session";

    private final DSLContext dsl;

    @Inject
    public SessionConcept(ActionLog actionLog, CompletionBus completionBus,
                          SyncEvaluator evaluator, DSLContext dsl) {
        super(actionLog, completionBus, evaluator);
        this.dsl = dsl;
    }

    /** Test-only constructor — sync evaluation bypassed for isolated tests. */
    public SessionConcept(ActionLog actionLog, CompletionBus completionBus, DSLContext dsl) {
        super(actionLog, completionBus);
        this.dsl = dsl;
    }

    @Override
    protected String conceptIRI() {
        return IRI;
    }

    @Override
    public void pollAll() {
        pollAndProcess("grant");
        pollAndProcess("lookup");
    }

    @Override
    protected void processInvocation(ActionRecord invocation) {
        switch (invocation.actionName()) {
            case "grant" -> doGrant(invocation);
            case "lookup" -> doLookup(invocation);
            default -> writeError(invocation, "unknown action: " + invocation.actionName());
        }
    }

    private void doGrant(ActionRecord invocation) {
        String userId = invocation.binding("userId");
        if (userId == null) {
            writeError(invocation, "missing userId");
            return;
        }
        String sessionId = UUID.randomUUID().toString();
        dsl.insertInto(SESSION_TOKENS, SESSION_TOKENS.SESSION_TOKEN, SESSION_TOKENS.USER_ID)
                .values(UUID.fromString(sessionId), UUID.fromString(userId))
                .execute();

        writeCompletion(invocation, Map.of(
                "outcome", ResourceFactory.createStringLiteral("GRANTED"),
                "sessionId", ResourceFactory.createStringLiteral(sessionId),
                "userId", ResourceFactory.createStringLiteral(userId)));
    }

    private void doLookup(ActionRecord invocation) {
        String sessionId = invocation.binding("sessionId");
        if (sessionId == null) {
            writeError(invocation, "missing sessionId");
            return;
        }
        UUID userId = dsl.select(SESSION_TOKENS.USER_ID).from(SESSION_TOKENS)
                .where(SESSION_TOKENS.SESSION_TOKEN.eq(UUID.fromString(sessionId)))
                .fetchOne(SESSION_TOKENS.USER_ID);
        if (userId == null) {
            writeCompletion(invocation, Map.of(
                    "outcome", ResourceFactory.createStringLiteral("UNKNOWN"),
                    "sessionId", ResourceFactory.createStringLiteral(sessionId)));
        } else {
            writeCompletion(invocation, Map.of(
                    "outcome", ResourceFactory.createStringLiteral("ACTIVE"),
                    "sessionId", ResourceFactory.createStringLiteral(sessionId),
                    "userId", ResourceFactory.createStringLiteral(userId.toString())));
        }
    }
}
