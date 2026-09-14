package dev.legible.example.login;

/**
 * Readable relay constants for the login sync rules: concept names come in via
 * the concept classes' own {@code NAME} constants, action names from those
 * classes' action constants, and the aliases here exist only because a
 * static-import alias is not expressible in Java. Nothing here is logic —
 * see {@code maintenance/sync-dsl-legibility.md}.
 */
public final class LoginNames {

    public static final String WEB = WebConcept.NAME;
    public static final String USER_NAMING = UserNamingConcept.NAME;
    public static final String PASSWORD_AUTH = PasswordAuthConcept.NAME;
    public static final String SESSION = SessionConcept.NAME;

    private LoginNames() {
    }
}
