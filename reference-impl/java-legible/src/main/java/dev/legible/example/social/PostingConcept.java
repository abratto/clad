package dev.legible.example.social;

import dev.legible.engine.Concept;
import dev.legible.engine.Region;

import java.util.Map;
import java.util.UUID;

/** Posts: who authored them. State: {@code author(postId) -> authorId}. */
public final class PostingConcept implements Concept {

    private final Region region;

    public PostingConcept(Region region) {
        this.region = region;
    }

    @Override
    public String name() {
        return "Posting";
    }

    @Override
    public Map<String, Object> execute(String action, Map<String, Object> input) {
        return switch (action) {
            case "createPost" -> createPost(input);
            default -> Map.of("outcome", "error", "message", "unknown action: " + action);
        };
    }

    public String authorOf(String postId) {
        var v = region.read(postId, "author");
        return v.isEmpty() ? null : v.iterator().next();
    }

    private Map<String, Object> createPost(Map<String, Object> input) {
        String author = (String) input.get("author");
        String content = (String) input.get("content");
        if (author == null || content == null) {
            return Map.of("outcome", "error", "message", "missing author or content");
        }
        String postId = UUID.randomUUID().toString();
        region.write(postId, "author", author);
        region.write(postId, "content", content);
        return Map.of("outcome", "CREATED", "postId", postId, "author", author, "content", content);
    }
}
