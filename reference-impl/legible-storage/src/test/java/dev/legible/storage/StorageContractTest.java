package dev.legible.storage;

import dev.legible.engine.FactStore;
import dev.legible.engine.Region;
import dev.legible.example.login.LoginApp;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * The storage-agnostic contract: every {@link FactStore} backend must satisfy
 * the SPI semantics, and the login feature must behave identically on each.
 */
abstract class StorageContractTest {

    abstract FactStore newStore();

    /** Optional per-test reset (e.g. TRUNCATE) — no-op by default. */
    void reset(FactStore store) {
    }

    private FactStore store;
    private LoginApp app;

    @BeforeEach
    void setUp() {
        store = newStore();
        reset(store);
        app = LoginApp.create(store);
    }

    // ------------------------------------------------------------------
    // SPI contract
    // ------------------------------------------------------------------

    @Test
    void readWriteRemoveClear() {
        Region r = store.region("C");
        r.write("s1", "p", "v1");
        r.write("s1", "p", "v2");
        assertEquals(Set.of("v1", "v2"), r.read("s1", "p"));
        r.remove("s1", "p", "v1");
        assertEquals(Set.of("v2"), r.read("s1", "p"));
        r.clear("s1", "p");
        assertTrue(r.read("s1", "p").isEmpty());
    }

    @Test
    void subjectsFanOut() {
        Region r = store.region("Follow");
        r.write("f1", "target", "post1");
        r.write("f2", "target", "post1");
        r.write("f3", "target", "post2");
        assertEquals(Set.of("f1", "f2"), r.subjects("target", "post1"));
    }

    @Test
    void factsEnumerateRegion() {
        Region r = store.region("C");
        r.write("s1", "p", "v1");
        assertEquals(1, r.facts().size());
        assertEquals("s1", r.facts().get(0).subject());
        assertEquals("p", r.facts().get(0).predicate());
        assertEquals("v1", r.facts().get(0).value());
    }

    @Test
    void regionsAreIsolated() {
        store.region("A").write("s", "p", "va");
        store.region("B").write("s", "p", "vb");
        assertEquals(Set.of("va"), store.region("A").read("s", "p"));
        assertEquals(Set.of("vb"), store.region("B").read("s", "p"));
    }

    /**
     * The negative state pattern's substrate. `absent(Concept ; subject ;
     * predicate)` is resolved by `Region.read` returning empty — so a durable
     * store must return empty for an optional predicate with no fact (a loan
     * with no `returnedAt`), and the value once one is written. A store that
     * materialised an optional role as a `NULL`-valued fact (rather than no
     * fact) would make `absent` fail closed against the wrong state.
     */
    @Test
    void absentPredicateReadsEmptyUntilWritten() {
        Region r = store.region("Lending");
        r.write("loan1", "borrower", "m1");

        assertTrue(r.read("loan1", "returnedAt").isEmpty(),
                "an optional predicate with no fact must read empty (absent)");
        assertEquals(Set.of("m1"), r.read("loan1", "borrower"),
                "the mandatory fact is unaffected");

        r.write("loan1", "returnedAt", "2026-01-01T00:00:00Z");
        assertEquals(Set.of("2026-01-01T00:00:00Z"), r.read("loan1", "returnedAt"),
                "once written, the optional fact is present");
    }

    // ------------------------------------------------------------------
    // Login parity (identical outcomes and field values across backends)
    // ------------------------------------------------------------------

    @Test
    void successfulLoginReturns200WithSessionToken() {
        app.seedUser("alice", "secret");
        Map<String, Object> res = app.login("alice", "secret");
        assertEquals(200, res.get("status"));
        assertNotNull(res.get("sessionToken"));
        assertTrue(res.get("sessionToken") instanceof String);
        assertTrue(!((String) res.get("sessionToken")).isEmpty());
    }

    @Test
    void wrongPasswordReturns401WithOpaqueMessage() {
        app.seedUser("alice", "secret");
        Map<String, Object> res = app.login("alice", "wrong");
        assertEquals(401, res.get("status"));
        assertEquals("username or password didn't match", res.get("message"));
    }

    @Test
    void unknownUserReturns401WithOpaqueMessage() {
        Map<String, Object> res = app.login("nobody", "whatever");
        assertEquals(401, res.get("status"));
        assertEquals("username or password didn't match", res.get("message"));
    }

    @Test
    void lockoutReturns401WithVisibleMessage() {
        app.seedUser("alice", "secret");
        for (int i = 0; i < 5; i++) {
            assertEquals(401, app.login("alice", "wrong").get("status"));
        }
        Map<String, Object> res = app.login("alice", "secret");
        assertEquals(401, res.get("status"));
        assertEquals("Too many attempts. Try again in 15 minutes.", res.get("message"));
    }
}
