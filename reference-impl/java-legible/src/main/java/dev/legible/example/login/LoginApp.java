package dev.legible.example.login;

import dev.legible.engine.Concept;
import dev.legible.engine.FactStore;
import dev.legible.engine.InMemoryFactStore;
import dev.legible.engine.Region;
import dev.legible.engine.SyncEngine;
import dev.legible.engine.SyncRule;

import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Wires the login application over the prototype engine: one in-memory fact
 * store, one in-memory action log, three business concepts + the Web bootstrap
 * concept, and the seven login syncs. The transport surface is
 * {@link #login(String, String)}.
 */
public final class LoginApp {

    private final SyncEngine engine;
    private final UserNamingConcept userNaming;
    private final PasswordAuthConcept passwordAuth;

    private LoginApp(SyncEngine engine, UserNamingConcept userNaming,
                     PasswordAuthConcept passwordAuth) {
        this.engine = engine;
        this.userNaming = userNaming;
        this.passwordAuth = passwordAuth;
    }

    public static LoginApp create() {
        return create(new InMemoryFactStore());
    }

    public static LoginApp create(FactStore facts) {
        Region userRegion = facts.region("UserNaming");
        Region pwRegion = facts.region("PasswordAuth");
        Region sessionRegion = facts.region("Session");

        UserNamingConcept userNaming = new UserNamingConcept(userRegion);
        PasswordAuthConcept passwordAuth = new PasswordAuthConcept(pwRegion);
        SessionConcept session = new SessionConcept(sessionRegion);

        List<Concept> concepts = List.of(new WebConcept(), userNaming, passwordAuth, session);
        List<SyncRule> rules = LoginSyncs.all();
        SyncEngine engine = new SyncEngine(facts, concepts, rules);
        return new LoginApp(engine, userNaming, passwordAuth);
    }

    /** Seed a registered user with a credential. */
    public void seedUser(String username, String password) {
        String userId = UUID.randomUUID().toString();
        userNaming.seedUser(userId, username);
        passwordAuth.seedCredential(userId, password);
    }

    /** Run the login flow. Returns the Web/respond fields ({@code status}, payload). */
    public Map<String, Object> login(String username, String password) {
        return engine.run("Web", "request", Map.of(
                "route", "login",
                "username", username,
                "password", password));
    }

    public SyncEngine engine() {
        return engine;
    }
}
