package dev.legible.example.token;

import dev.legible.engine.Concept;
import dev.legible.engine.FactStore;
import dev.legible.engine.InMemoryFactStore;
import dev.legible.engine.SyncEngine;
import dev.legible.engine.SyncRule;
import dev.legible.example.login.WebConcept;

import java.util.List;
import java.util.Map;

/** Wires the token-issuing feature over the prototype engine (reuses Web). */
public final class TokenApp {

    private final SyncEngine engine;
    private final TokenConcept token;

    private TokenApp(SyncEngine engine, TokenConcept token) {
        this.engine = engine;
        this.token = token;
    }

    public static TokenApp create() {
        FactStore facts = new InMemoryFactStore();
        TokenConcept token = new TokenConcept(facts.region("Token"));
        List<Concept> concepts = List.of(new WebConcept(), token);
        List<SyncRule> rules = TokenSyncs.all();
        SyncEngine engine = new SyncEngine(facts, concepts, rules);
        return new TokenApp(engine, token);
    }

    public SyncEngine engine() {
        return engine;
    }

    public Map<String, Object> issue(String userId) {
        return engine.run("Web", "request", Map.of("route", "issue", "userId", userId));
    }

    public String ownerOf(String tokenId) {
        return token.ownerOf(tokenId);
    }
}
