package com.example.app.concepts.user;

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

import static com.example.app.db.tables.UserAccounts.USER_ACCOUNTS;

/**
 * The User concept: who exists in the system.
 *
 * <p>State lives in the {@code user_accounts} table (concept-owned). Two actions:
 * <ul>
 *   <li>{@code register} — adds a (userId, username) record.</li>
 *   <li>{@code lookupByUsername} — emits {@code outcome=FOUND|UNKNOWN}.</li>
 * </ul>
 *
 * <p>Coordination goes through the shared in-memory action log; only concept
 * state is relational (JOOQ over Postgres).
 */
@Singleton
public final class UserConcept extends ConceptAgent {

    /** IRI used in :concept triples. */
    public static final String IRI = "https://clad.dev/concept/user";

    private final DSLContext dsl;

    @Inject
    public UserConcept(ActionLog actionLog, CompletionBus completionBus,
                       SyncEvaluator evaluator, DSLContext dsl) {
        super(actionLog, completionBus, evaluator);
        this.dsl = dsl;
    }

    /** Test-only constructor — sync evaluation bypassed for isolated tests. */
    public UserConcept(ActionLog actionLog, CompletionBus completionBus, DSLContext dsl) {
        super(actionLog, completionBus);
        this.dsl = dsl;
    }

    @Override
    protected String conceptIRI() {
        return IRI;
    }

    @Override
    public void pollAll() {
        pollAndProcess("register");
        pollAndProcess("lookupByUsername");
    }

    @Override
    protected void processInvocation(ActionRecord invocation) {
        switch (invocation.actionName()) {
            case "register" -> doRegister(invocation);
            case "lookupByUsername" -> doLookup(invocation);
            default -> writeError(invocation, "unknown action: " + invocation.actionName());
        }
    }

    /** Test/seed helper to pre-populate the user table. */
    public void seedUser(String userId, String username) {
        dsl.insertInto(USER_ACCOUNTS, USER_ACCOUNTS.USER_ID, USER_ACCOUNTS.USERNAME)
                .values(UUID.fromString(userId), username)
                .onConflictDoNothing()
                .execute();
    }

    private void doRegister(ActionRecord invocation) {
        String username = invocation.binding("username");
        if (username == null) { writeError(invocation, "missing username"); return; }
        if (existsByUsername(username)) {
            writeRefusal(invocation, "username already taken: " + username);
            return;
        }
        String userId = UUID.randomUUID().toString();
        seedUser(userId, username);
        writeCompletion(invocation, Map.of(
                "outcome", ResourceFactory.createStringLiteral("REGISTERED"),
                "userId", ResourceFactory.createStringLiteral(userId),
                "username", ResourceFactory.createStringLiteral(username)));
    }

    private void doLookup(ActionRecord invocation) {
        String username = invocation.binding("username");
        if (username == null) { writeError(invocation, "missing username"); return; }
        String userId = findUserIdByUsername(username);
        if (userId == null) {
            writeRefusal(invocation, "username not found: " + username);
        } else {
            writeCompletion(invocation, Map.of(
                    "outcome", ResourceFactory.createStringLiteral("FOUND"),
                    "userId", ResourceFactory.createStringLiteral(userId),
                    "username", ResourceFactory.createStringLiteral(username)));
        }
    }

    private boolean existsByUsername(String username) {
        return dsl.fetchExists(dsl.selectOne().from(USER_ACCOUNTS)
                .where(USER_ACCOUNTS.USERNAME.eq(username)));
    }

    private String findUserIdByUsername(String username) {
        UUID userId = dsl.select(USER_ACCOUNTS.USER_ID).from(USER_ACCOUNTS)
                .where(USER_ACCOUNTS.USERNAME.eq(username))
                .fetchOne(USER_ACCOUNTS.USER_ID);
        return userId == null ? null : userId.toString();
    }
}
