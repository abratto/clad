package dev.legible.example.social;

import dev.legible.engine.Concept;
import dev.legible.engine.Region;

import java.util.Map;
import java.util.UUID;

/** Comments on posts. State: {@code post(commentId) -> postId}. */
public final class CommentingConcept implements Concept {

    private final Region region;

    public CommentingConcept(Region region) {
        this.region = region;
    }

    @Override
    public String name() {
        return "Commenting";
    }

    @Override
    public Map<String, Object> execute(String action, Map<String, Object> input) {
        return switch (action) {
            case "comment" -> comment(input);
            default -> Map.of("outcome", "error", "message", "unknown action: " + action);
        };
    }

    private Map<String, Object> comment(Map<String, Object> input) {
        String postId = (String) input.get("postId");
        String author = (String) input.get("author");
        String text = (String) input.get("text");
        if (postId == null || author == null || text == null) {
            return Map.of("outcome", "error", "message", "missing postId, author or text");
        }
        String commentId = UUID.randomUUID().toString();
        region.write(commentId, "post", postId);
        return Map.of("outcome", "COMMENTED", "commentId", commentId, "postId", postId, "author", author);
    }
}
