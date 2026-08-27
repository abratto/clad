package dev.legible.example.login;

import dev.legible.engine.Concept;
import dev.legible.engine.Region;

import java.util.Map;
import java.util.Set;

/**
 * Verifies a principal by {@code userId + password}. State is the relations
 * {@code passwordHash}, {@code failedAttempts}, {@code lockedUntil} over
 * {@code UserId}, held in this concept's own region.
 */
public final class PasswordAuthConcept implements Concept {

    private static final int LOCKOUT_THRESHOLD = 5;
    private static final long LOCKOUT_WINDOW_MILLIS = 15L * 60L * 1000L;

    private final Region region;

    public PasswordAuthConcept(Region region) {
        this.region = region;
    }

    @Override
    public String name() {
        return "PasswordAuth";
    }

    @Override
    public Map<String, Object> execute(String action, Map<String, Object> input) {
        return switch (action) {
            case "setCredential" -> setCredential(input);
            case "check" -> check(input);
            default -> Map.of("outcome", "error", "message", "unknown action: " + action);
        };
    }

    /** Test/seed helper. */
    public void seedCredential(String userId, String password) {
        region.clear(userId, "passwordHash");
        region.clear(userId, "failedAttempts");
        region.clear(userId, "lockedUntil");
        region.write(userId, "passwordHash", verify(password));
    }

    private Map<String, Object> setCredential(Map<String, Object> input) {
        String userId = (String) input.get("userId");
        String password = (String) input.get("password");
        if (userId == null || password == null) {
            return Map.of("outcome", "error", "message", "missing userId or password");
        }
        seedCredential(userId, password);
        return Map.of("outcome", "SET", "userId", userId);
    }

    private Map<String, Object> check(Map<String, Object> input) {
        String userId = (String) input.get("userId");
        String password = (String) input.get("password");
        if (userId == null || password == null) {
            return Map.of("outcome", "error", "message", "missing userId or password");
        }
        Set<String> verifiers = region.read(userId, "passwordHash");
        if (verifiers.isEmpty()) {
            return Map.of("outcome", "NO_CREDENTIAL", "userId", userId);
        }
        String verifier = verifiers.iterator().next();
        long now = System.currentTimeMillis();

        Set<String> locked = region.read(userId, "lockedUntil");
        if (!locked.isEmpty() && Long.parseLong(locked.iterator().next()) > now) {
            return Map.of("outcome", "LOCKED", "userId", userId);
        }
        if (verifier.equals(verify(password))) {
            clearAttempts(userId);
            return Map.of("outcome", "OK", "userId", userId);
        }
        int failed = currentFailed(userId) + 1;
        Long lockedUntil = failed >= LOCKOUT_THRESHOLD ? now + LOCKOUT_WINDOW_MILLIS : null;
        recordFailure(userId, failed, lockedUntil);
        return Map.of("outcome", "BAD_PASSWORD", "userId", userId);
    }

    private void clearAttempts(String userId) {
        region.clear(userId, "failedAttempts");
        region.clear(userId, "lockedUntil");
    }

    private int currentFailed(String userId) {
        Set<String> f = region.read(userId, "failedAttempts");
        return f.isEmpty() ? 0 : Integer.parseInt(f.iterator().next());
    }

    private void recordFailure(String userId, int failed, Long lockedUntil) {
        region.clear(userId, "failedAttempts");
        region.write(userId, "failedAttempts", String.valueOf(failed));
        region.clear(userId, "lockedUntil");
        if (lockedUntil != null) {
            region.write(userId, "lockedUntil", String.valueOf(lockedUntil));
        }
    }

    /** Trivial verifier — DO NOT USE IN PRODUCTION. */
    private static String verify(String password) {
        return "sha256:" + Integer.toHexString(password.hashCode());
    }
}
