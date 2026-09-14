package com.example.app.syncs;

import dev.legible.engine.SyncRule;

import java.util.List;

/**
 * Assembles the seven login synchronization rules authored in this profile.
 * One class per {@code *.sync.md} (v2 effect-first names — see
 * maintenance/sync-dsl-legibility.md); one rule per class, the declarative
 * {@code SyncRule} realization of Stage 03.
 */
public final class LoginSyncRules {

    private LoginSyncRules() {
    }

    public static List<SyncRule> all() {
        return List.of(
                new UserNamingLookupByUsernameForLoginWhenWebRequestRouted().rule(),
                new PasswordAuthCheckForLoginWhenUserNamingLookupByUsernameFound().rule(),
                new WebRespondForLoginWhenUserNamingLookupByUsernameRefused().rule(),
                new SessionGrantForLoginWhenPasswordAuthCheckOk().rule(),
                new WebRespondForLoginWhenPasswordAuthCheckBadPassword().rule(),
                new WebRespondForLoginWhenPasswordAuthCheckLocked().rule(),
                new WebRespondForLoginWhenSessionGrantGranted().rule());
    }
}
