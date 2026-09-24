package com.example.app.engine;

import com.example.app.concepts.passwordauth.PasswordAuthConcept;
import com.example.app.concepts.session.SessionConcept;
import com.example.app.concepts.usernaming.UserNamingConcept;
import com.example.app.concepts.web.WebConcept;
import com.example.app.syncs.LoginSyncRules;
import dev.legible.engine.Concept;
import dev.legible.engine.FactStore;
import dev.legible.engine.SyncEngine;
import io.micronaut.context.annotation.Factory;
import jakarta.inject.Singleton;

import java.util.List;

/**
 * Wires the fire-after-commit engine over the active {@link FactStore}: the Web
 * bootstrap plus the three business concepts, and the seven login syncs as
 * declarative rules.
 *
 * <p>Backend-agnostic by design — it depends only on the engine's
 * {@code FactStore} SPI. Which concrete store is injected (in-memory or
 * Postgres) is decided by the storage binding
 * (see {@code com.example.app.storage}); the concepts and syncs are identical.
 */
@Factory
public final class CladEngineFactory {

    @Singleton
    public SyncEngine syncEngine(FactStore facts) {
        WebConcept web = new WebConcept();
        UserNamingConcept userNaming = new UserNamingConcept(facts.region("UserNaming"));
        PasswordAuthConcept passwordAuth = new PasswordAuthConcept(facts.region("PasswordAuth"));
        SessionConcept session = new SessionConcept(facts.region("Session"));
        List<Concept> concepts = List.of(web, userNaming, passwordAuth, session);
        return new SyncEngine(facts, concepts, LoginSyncRules.all());
    }

    @Singleton
    public LoginGateway loginGateway(SyncEngine engine) {
        return new LoginGateway(engine);
    }
}
