package com.example.app;

import com.example.app.concepts.passwordauth.PasswordAuthConcept;
import com.example.app.concepts.user.UserConcept;
import io.micronaut.context.event.StartupEvent;
import io.micronaut.runtime.Micronaut;
import io.micronaut.runtime.event.annotation.EventListener;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;

/** Micronaut bootstrap. */
public class Application {
    public static void main(String[] args) {
        Micronaut.run(Application.class, args);
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
