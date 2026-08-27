package dev.legible.example.token;

import dev.legible.engine.Concept;
import dev.legible.engine.Region;

import java.util.Map;

/**
 * Issues tokens whose id is minted by the calling sync — not by this concept.
 * State: {@code owner(tokenId) -> userId}. The {@code issue} action records the
 * id it is handed; it never generates one itself.
 */
public final class TokenConcept implements Concept {

    private final Region region;

    public TokenConcept(Region region) {
        this.region = region;
    }

    @Override
    public String name() {
        return "Token";
    }

    @Override
    public Map<String, Object> execute(String action, Map<String, Object> input) {
        return switch (action) {
            case "issue" -> issue(input);
            default -> Map.of("outcome", "error", "message", "unknown action: " + action);
        };
    }

    public String ownerOf(String tokenId) {
        var v = region.read(tokenId, "owner");
        return v.isEmpty() ? null : v.iterator().next();
    }

    private Map<String, Object> issue(Map<String, Object> input) {
        String tokenId = (String) input.get("tokenId");
        String userId = (String) input.get("userId");
        if (tokenId == null || userId == null) {
            return Map.of("outcome", "error", "message", "missing tokenId or userId");
        }
        region.write(tokenId, "owner", userId);
        return Map.of("outcome", "ISSUED", "tokenId", tokenId, "userId", userId);
    }
}
