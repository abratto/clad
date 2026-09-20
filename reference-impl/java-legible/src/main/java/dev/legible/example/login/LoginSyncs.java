package dev.legible.example.login;

import dev.legible.engine.SyncRule;

import java.util.List;
import java.util.Map;

import static dev.legible.engine.Dsl.args;
import static dev.legible.engine.Dsl.bind;
import static dev.legible.engine.Dsl.conj;
import static dev.legible.engine.Dsl.invoke;
import static dev.legible.engine.Dsl.lit;
import static dev.legible.engine.Dsl.ref;
import static dev.legible.engine.Dsl.rule;
import static dev.legible.engine.Dsl.siblingInput;
import static dev.legible.engine.Dsl.triggerField;
import static dev.legible.engine.Dsl.triggerInput;
import static dev.legible.example.login.LoginNames.PASSWORD_AUTH;
import static dev.legible.example.login.LoginNames.SESSION;
import static dev.legible.example.login.LoginNames.USER_NAMING;
import static dev.legible.example.login.LoginNames.WEB;
import static dev.legible.example.login.PasswordAuthConcept.CHECK;
import static dev.legible.example.login.SessionConcept.GRANT;
import static dev.legible.example.login.UserNamingConcept.LOOKUP_BY_USERNAME;
import static dev.legible.example.login.WebConcept.REQUEST;
import static dev.legible.example.login.WebConcept.RESPOND;

/**
 * The seven login synchronizations, expressed paper-faithfully as
 * {@code when → where → then} rules through the fluent DSL. Each maps 1:1 to a
 * Stage 03 {@code *.sync.md}; the only change from the original Jena profile
 * was the bootstrap concept name ({@code Web/request} for {@code Web/handle}).
 *
 * <p>Names follow the effect-first grammar (see
 * {@code maintenance/sync-dsl-legibility.md}):
 * {@code <TargetConcept><TargetAction>[For<Scope>]When<TriggerConcept><TriggerAction><TriggerCompletion>}.
 * All {@code Web/request} rules carry {@code route} as a {@code when}-matcher,
 * so the disjoint route scopes are visible before the body is even read.
 */
public final class LoginSyncs {

    private LoginSyncs() {
    }

    public static List<SyncRule> all() {
        return List.of(
                lookupByUsernameWhenRequestRouted(),
                checkWhenLookupByUsernameFound(),
                respondWhenLookupByUsernameRefused(),
                grantWhenCheckOk(),
                respondWhenCheckBadPassword(),
                respondWhenCheckLocked(),
                respondWhenGrantGranted());
    }

    /** Row 1→2: when Web/request[routed] → UserNaming.lookupByUsername(username). */
    private static SyncRule lookupByUsernameWhenRequestRouted() {
        return rule("LookupByUsernameForLoginWhenRequestRouted")
            .when(WEB, REQUEST, "routed")
            .matching(Map.of("route", "login"))
            .where(bind("?u", triggerInput("username")))
            .then(invoke(USER_NAMING, LOOKUP_BY_USERNAME, args("username", ref("?u"))))
            .build();
    }

    /** Row 2[Found]→3b: when UserNaming.lookupByUsername[FOUND] → PasswordAuth.check(userId, password). */
    private static SyncRule checkWhenLookupByUsernameFound() {
        return rule("CheckWhenLookupByUsernameFound")
            .when(conj("trigger", USER_NAMING, LOOKUP_BY_USERNAME, "FOUND"))
            .and(conj("requested", WEB, REQUEST, "routed").matching(Map.of("route", "login")))
            .where(bind("?user", triggerField("userId")),
                   bind("?p", siblingInput(WEB, REQUEST, "password")))
            .then(invoke(PASSWORD_AUTH, CHECK,
                    args("userId", ref("?user"), "password", ref("?p"))))
            .build();
    }

    /** Row 2[refused]→3a: when UserNaming.lookupByUsername[refused] → Web.respond(401, opaque message). */
    private static SyncRule respondWhenLookupByUsernameRefused() {
        return rule("RespondWhenLookupByUsernameRefused")
            .when(conj("trigger", USER_NAMING, LOOKUP_BY_USERNAME, "refused"))
            .and(conj("requested", WEB, REQUEST, "routed").matching(Map.of("route", "login")))
            .then(invoke(WEB, RESPOND, args(
                    "status", lit(401),
                    "message", lit("username or password didn't match"))))
            .build();
    }

    /** Row 3b[OK]→4a: when PasswordAuth.check[OK] → Session.grant(userId). */
    private static SyncRule grantWhenCheckOk() {
        return rule("GrantWhenCheckOk")
            .when(conj("trigger", PASSWORD_AUTH, CHECK, "OK"))
            .and(conj("requested", WEB, REQUEST, "routed").matching(Map.of("route", "login")))
            .where(bind("?user", triggerField("userId")))
            .then(invoke(SESSION, GRANT, args("userId", ref("?user"))))
            .build();
    }

    /** Row 3b[BAD_PASSWORD]→4b: respond 401 opaque. */
    private static SyncRule respondWhenCheckBadPassword() {
        return rule("RespondWhenCheckBadPassword")
            .when(conj("trigger", PASSWORD_AUTH, CHECK, "BAD_PASSWORD"))
            .and(conj("requested", WEB, REQUEST, "routed").matching(Map.of("route", "login")))
            .then(invoke(WEB, RESPOND, args(
                    "status", lit(401),
                    "message", lit("username or password didn't match"))))
            .build();
    }

    /** Row 3b[LOCKED]→4c: respond 401 with the visible lockout message. */
    private static SyncRule respondWhenCheckLocked() {
        return rule("RespondWhenCheckLocked")
            .when(conj("trigger", PASSWORD_AUTH, CHECK, "LOCKED"))
            .and(conj("requested", WEB, REQUEST, "routed").matching(Map.of("route", "login")))
            .then(invoke(WEB, RESPOND, args(
                    "status", lit(401),
                    "message", lit("Too many attempts. Try again in 15 minutes."))))
            .build();
    }

    /** Row 4a[GRANTED]→5: when Session.grant[GRANTED] → Web.respond(200, sessionToken). */
    private static SyncRule respondWhenGrantGranted() {
        return rule("RespondWhenGrantGranted")
            .when(conj("trigger", SESSION, GRANT, "GRANTED"))
            .and(conj("requested", WEB, REQUEST, "routed").matching(Map.of("route", "login")))
            .where(bind("?sid", triggerField("sessionId")))
            .then(invoke(WEB, RESPOND, args(
                    "status", lit(200),
                    "sessionToken", ref("?sid"))))
            .build();
    }
}
