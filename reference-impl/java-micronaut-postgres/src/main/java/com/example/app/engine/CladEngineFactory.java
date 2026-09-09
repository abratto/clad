package com.example.app.engine;

import com.example.app.concepts.passwordauth.PasswordAuthConcept;
import com.example.app.concepts.session.SessionConcept;
import com.example.app.concepts.usernaming.UserNamingConcept;
import com.example.app.concepts.web.WebConcept;
import com.example.app.syncs.LoginSyncRules;
import dev.legible.engine.Concept;
import dev.legible.engine.FactStore;
import dev.legible.engine.SyncEngine;
import dev.legible.storage.RmapPostgresFactStore;
import dev.legible.storage.RelationSchema;
import dev.legible.storage.LoginSchemas;
import io.micronaut.context.annotation.Factory;
import jakarta.inject.Singleton;

import java.util.ArrayList;
import java.util.List;

import javax.sql.DataSource;

/**
 * Wires the fire-after-commit engine over Postgres-backed concept state:
 * one {@link RmapPostgresFactStore} whose schemas derive from the Stage 03b
 * data models ({@link LoginSchemas}), the Web bootstrap plus the three
 * business concepts, and the seven login syncs as declarative rules.
 */
@Factory
public final class CladEngineFactory {

    @Singleton
    public RmapPostgresFactStore factStore(DataSource dataSource) {
        List<RelationSchema> schemas = new ArrayList<>(LoginSchemas.all());
        return new RmapPostgresFactStore(dataSource, schemas);
    }

    @Singleton
    public SyncEngine syncEngine(RmapPostgresFactStore facts) {
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
