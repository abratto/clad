package com.example.app;

import com.example.app.concepts.passwordauth.PasswordAuthConcept;
import com.example.app.concepts.user.UserConcept;
import com.example.app.engine.ActionLog;
import io.micronaut.context.event.StartupEvent;
import io.micronaut.runtime.Micronaut;
import io.micronaut.runtime.event.annotation.EventListener;
import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.info.Info;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;

import java.io.FileInputStream;
import java.util.Properties;

/** Micronaut bootstrap. */
@OpenAPIDefinition(
        info = @Info(
                title = "CLAD Java Reference API",
                version = "0.1.0",
                description = "Transport-facing REST surface for the CLAD Java/Jena/Micronaut reference profile. This OpenAPI document is derived from the Web boundary and remains subordinate to CLAD use case, concept, sync, and SPEC artefacts."))
public class Application {
    public static void main(String[] args) {
        Micronaut.run(Application.class, args);
    }

    /**
     * Reads engine configuration from {@code clad.properties} at startup.
     */
    @Singleton
    public static class EngineConfig {
        private final ActionLog actionLog;

        @Inject
        public EngineConfig(ActionLog actionLog) {
            this.actionLog = actionLog;
        }

        @EventListener
        void onStartup(StartupEvent event) {
            boolean archiveFlows = readProperty("engine.archive.flows", "true").equals("true");
            actionLog.setArchiveEnabled(archiveFlows);
        }

        private static String readProperty(String key, String defaultValue) {
            try (FileInputStream in = new FileInputStream("clad.properties")) {
                Properties props = new Properties();
                props.load(in);
                return props.getProperty(key, defaultValue);
            } catch (Exception e) {
                return defaultValue;
            }
        }
    }

    /**
     * Seeds a single demo user "ada" with a known password at startup so the
     * reference profile is runnable out of the box. Production profiles would
     * remove this and load credentials from a real source.
     */
    @Singleton
    public static class DemoSeed {
        private final UserConcept users;
        private final PasswordAuthConcept passwords;

        @Inject
        public DemoSeed(UserConcept users, PasswordAuthConcept passwords) {
            this.users = users;
            this.passwords = passwords;
        }

        @EventListener
        void onStartup(StartupEvent event) {
            String userId = "ada-0001";
            users.seedUser(userId, "ada");
            passwords.seedCredential(userId, "correct-horse-battery-staple");
        }
    }
}
