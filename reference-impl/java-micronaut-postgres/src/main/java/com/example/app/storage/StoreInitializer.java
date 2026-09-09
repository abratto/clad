package com.example.app.storage;

import com.example.app.concepts.passwordauth.PasswordAuthConcept;
import com.example.app.concepts.session.SessionConcept;
import com.example.app.concepts.usernaming.UserNamingConcept;
import dev.legible.storage.RmapPostgresFactStore;
import io.micronaut.context.event.StartupEvent;
import io.micronaut.runtime.event.annotation.EventListener;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;
import org.flywaydb.core.Flyway;

import javax.sql.DataSource;

/**
 * Applies base DDL at startup, in one deterministic order:
 *
 * <ol>
 *   <li>Flyway owns the migration timeline ({{@code V1__login_rmap.sql}}
 *       documents the R-map base).</li>
 *   <li>{@link RmapPostgresFactStore#createSchema()} derives each concept's
 *       region table from the Stage 03b data models (idempotent, so tests may
 *       also call it directly).</li>
 *   <li>Then (and only then) the demo seed registers {@code ada} — every
 *       runtime consumer of the facts is ordered after the DDL owners.</li>
 * </ol>
 */
@Singleton
public class StoreInitializer {

    private final DataSource dataSource;
    private final RmapPostgresFactStore factStore;

    @Inject
    public StoreInitializer(DataSource dataSource, RmapPostgresFactStore factStore) {
        this.dataSource = dataSource;
        this.factStore = factStore;
    }

    @EventListener
    void onStartup(StartupEvent event) {
        Flyway.configure()
                .dataSource(dataSource)
                .load()
                .migrate();
        factStore.createSchema();
        seedDemoUser();
    }

    private void seedDemoUser() {
        String userId = "ada00001-0000-0000-0000-000000000001";
        new UserNamingConcept(factStore.region("UserNaming")).seedUser(userId, "ada");
        new PasswordAuthConcept(factStore.region("PasswordAuth"))
                .seedCredential(userId, "correct-horse-battery-staple");
    }
}
