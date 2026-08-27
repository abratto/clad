package dev.legible.example.social;

import dev.legible.engine.Concept;
import dev.legible.engine.FactStore;
import dev.legible.engine.InMemoryFactStore;
import dev.legible.engine.SyncEngine;
import dev.legible.engine.SyncRule;
import dev.legible.example.login.WebConcept;

import java.util.List;
import java.util.Map;

/** Wires the social feature over the prototype engine (reuses the Web bootstrap concept). */
public final class SocialApp {

    private final SyncEngine engine;
    private final FollowingConcept following;
    private final NotifyingConcept notifying;
    private final FeedConcept feed;
    private final PostingConcept posting;

    private SocialApp(SyncEngine engine, PostingConcept posting, FollowingConcept following,
                      NotifyingConcept notifying, FeedConcept feed) {
        this.engine = engine;
        this.posting = posting;
        this.following = following;
        this.notifying = notifying;
        this.feed = feed;
    }

    public static SocialApp create() {
        FactStore facts = new InMemoryFactStore();
        PostingConcept posting = new PostingConcept(facts.region("Posting"));
        CommentingConcept commenting = new CommentingConcept(facts.region("Commenting"));
        FollowingConcept following = new FollowingConcept(facts.region("Following"));
        NotifyingConcept notifying = new NotifyingConcept(facts.region("Notifying"));
        FeedConcept feed = new FeedConcept(facts.region("Feed"));

        List<Concept> concepts = List.of(new WebConcept(), posting, commenting, following, notifying, feed);
        List<SyncRule> rules = SocialSyncs.all();
        SyncEngine engine = new SyncEngine(facts, concepts, rules);
        return new SocialApp(engine, posting, following, notifying, feed);
    }

    public SyncEngine engine() {
        return engine;
    }

    public Map<String, Object> publish(String author, String content) {
        return engine.run("Web", "request", Map.of("route", "publish", "author", author, "content", content));
    }

    public Map<String, Object> comment(String postId, String author, String text) {
        return engine.run("Web", "request", Map.of("route", "comment", "postId", postId, "author", author, "text", text));
    }

    public Map<String, Object> follow(String follower, String target) {
        return engine.run("Web", "request", Map.of("route", "follow", "follower", follower, "target", target));
    }

    public void seedFollow(String follower, String target) {
        following.seedFollow(follower, target);
    }

    public String postAuthor(String postId) {
        return posting.authorOf(postId);
    }

    public List<String> notificationsFor(String userId) {
        return notifying.notificationsFor(userId);
    }

    public List<String> feedFor(String userId) {
        return feed.itemsFor(userId);
    }
}
