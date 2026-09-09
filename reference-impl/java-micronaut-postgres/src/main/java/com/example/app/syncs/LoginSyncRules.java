package com.example.app.syncs;

import dev.legible.engine.SyncRule;

import java.util.List;

/**
 * Assembles the seven login synchronization rules authored in this profile.
 * One class per {@code *.sync.md} — one rule per class, the declarative
 * {@code SyncRule} realization of Stage 03.
 */
public final class LoginSyncRules {

    private LoginSyncRules() {
    }

    public static List<SyncRule> all() {
        return List.of(
                new WhenWebRequestRoutedThenUserNamingLookupByUsernameForLogin().rule(),
                new WhenUserNamingLookupByUsernameFoundThenPasswordAuthCheckForLogin().rule(),
                new WhenUserNamingLookupByUsernameRefusedThenWebRespondForLogin().rule(),
                new WhenPasswordAuthCheckOkThenSessionGrantForLogin().rule(),
                new WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin().rule(),
                new WhenPasswordAuthCheckLockedThenWebRespondForLogin().rule(),
                new WhenSessionGrantGrantedThenWebRespondForLogin().rule());
    }
}
