package dev.legible.example.login;

import dev.legible.engine.Clause;
import dev.legible.engine.Source;
import dev.legible.engine.SyncRule;
import dev.legible.engine.ThenInvocation;

import java.util.List;
import java.util.Map;

import static dev.legible.engine.SyncRule.invoke;
import static dev.legible.engine.SyncRule.lit;
import static dev.legible.engine.SyncRule.ref;

/**
 * The seven login synchronizations, re-expressed paper-faithfully as
 * {@code when}/{@code where}/{@code then} rules. Each maps 1:1 to a Stage 03
 * {@code *.sync.md}. The only change from the Jena profile is the bootstrap
 * concept: {@code Web/request} (the paper's name) replaces {@code Web/handle},
 * collapsing the old "bootstrap handoff exception".
 */
public final class LoginSyncs {

    private LoginSyncs() {
    }

    public static List<SyncRule> all() {
        return List.of(
                webRequestRoutedToLookup(),
                lookupFoundToCheck(),
                lookupRefusedToRespond(),
                checkOkToGrant(),
                checkBadPasswordToRespond(),
                checkLockedToRespond(),
                grantGrantedToRespond());
    }

    /** Row 1→2: when Web/request[routed] → UserNaming.lookupByUsername(username). */
    static SyncRule webRequestRoutedToLookup() {
        return SyncRule.of(
                "WhenWebRequestRoutedThenUserNamingLookupByUsernameForLogin",
                "Web", "request", "routed",
                List.of(new Clause.Bind("?u", new Source.TriggerInput("username"))),
                List.of(invoke("UserNaming", "lookupByUsername", Map.of("username", ref("?u")))));
    }

    /** Row 2[Found]→3b: when UserNaming.lookupByUsername[FOUND] → PasswordAuth.check(userId, password). */
    static SyncRule lookupFoundToCheck() {
        return SyncRule.of(
                "WhenUserNamingLookupByUsernameFoundThenPasswordAuthCheckForLogin",
                "UserNaming", "lookupByUsername", "FOUND",
                List.of(
                        new Clause.Bind("?user", new Source.TriggerField("userId")),
                        new Clause.Bind("?p", new Source.SiblingInput("Web", "request", "password"))),
                List.of(invoke("PasswordAuth", "check",
                        Map.of("userId", ref("?user"), "password", ref("?p")))));
    }

    /** Row 2[refused]→3a: when UserNaming.lookupByUsername[refused] → Web.respond(401, opaque message). */
    static SyncRule lookupRefusedToRespond() {
        return SyncRule.of(
                "WhenUserNamingLookupByUsernameRefusedThenWebRespondForLogin",
                "UserNaming", "lookupByUsername", "refused",
                List.of(),
                List.of(respond(401, "username or password didn't match", null)));
    }

    /** Row 3b[OK]→4a: when PasswordAuth.check[OK] → Session.grant(userId). */
    static SyncRule checkOkToGrant() {
        return SyncRule.of(
                "WhenPasswordAuthCheckOkThenSessionGrantForLogin",
                "PasswordAuth", "check", "OK",
                List.of(new Clause.Bind("?user", new Source.TriggerField("userId"))),
                List.of(invoke("Session", "grant", Map.of("userId", ref("?user")))));
    }

    /** Row 3b[BAD_PASSWORD]→4b: respond 401 opaque. */
    static SyncRule checkBadPasswordToRespond() {
        return SyncRule.of(
                "WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin",
                "PasswordAuth", "check", "BAD_PASSWORD",
                List.of(),
                List.of(respond(401, "username or password didn't match", null)));
    }

    /** Row 3b[LOCKED]→4c: respond 401 with the visible lockout message. */
    static SyncRule checkLockedToRespond() {
        return SyncRule.of(
                "WhenPasswordAuthCheckLockedThenWebRespondForLogin",
                "PasswordAuth", "check", "LOCKED",
                List.of(),
                List.of(respond(401, "Too many attempts. Try again in 15 minutes.", null)));
    }

    /** Row 4a[GRANTED]→5: when Session.grant[GRANTED] → Web.respond(200, sessionToken). */
    static SyncRule grantGrantedToRespond() {
        return SyncRule.of(
                "WhenSessionGrantGrantedThenWebRespondForLogin",
                "Session", "grant", "GRANTED",
                List.of(new Clause.Bind("?sid", new Source.TriggerField("sessionId"))),
                List.of(respond(200, null, "?sid")));
    }

    private static ThenInvocation respond(int status, String message, String sessionTokenVar) {
        Map<String, Source> args = new java.util.LinkedHashMap<>();
        args.put("status", lit(status));
        if (message != null) {
            args.put("message", lit(message));
        }
        if (sessionTokenVar != null) {
            args.put("sessionToken", ref(sessionTokenVar));
        }
        return invoke("Web", "respond", args);
    }
}
