package dev.legible.engine;

import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Absent-input matcher semantics (maintenance/engine-absent-input-matcher.md):
 * the {@code Dsl.ABSENT} sentinel requires the matched key to be ABSENT from
 * the trigger input; a value matcher keeps requiring key-present+equal.
 */
class WhenInputPatternTest {

    @Test
    void valueMatcherRequiresPresentAndEqual() {
        Map<String, Object> pattern = Map.of("route", "profile");
        assertTrue(SyncEngine.patternMatches(pattern, Map.of("route", "profile")));
        assertFalse(SyncEngine.patternMatches(pattern, Map.of("route", "other")));
        assertFalse(SyncEngine.patternMatches(pattern, Map.of("token", "t")));
    }

    @Test
    void absentSentinelMatchesOnlyWhenKeyIsAbsent() {
        Map<String, Object> pattern = Map.of("email", Dsl.ABSENT,
                                             "username", Dsl.ABSENT);
        // BOTH unique values absent → fires
        assertTrue(SyncEngine.patternMatches(pattern, Map.of("userId", "u-77")));
        // EITHER value present → does not fire
        assertFalse(SyncEngine.patternMatches(pattern,
                Map.of("userId", "u-77", "email", "e@new")));
        assertFalse(SyncEngine.patternMatches(pattern,
                Map.of("userId", "u-77", "username", "n@new")));
    }
}
