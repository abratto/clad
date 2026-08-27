package dev.legible.example.tagging;

import dev.legible.engine.Concept;
import dev.legible.engine.FactStore;
import dev.legible.engine.InMemoryFactStore;
import dev.legible.engine.SyncEngine;
import dev.legible.engine.SyncRule;
import dev.legible.example.login.WebConcept;
import dev.legible.example.social.NotifyingConcept;
import dev.legible.example.social.PostingConcept;

import java.util.List;
import java.util.Map;

/** Wires the tagging feature over the prototype engine (reuses Web, Posting, Notifying). */
public final class TaggingApp {

    private final SyncEngine engine;
    private final NotifyingConcept notifying;

    private TaggingApp(SyncEngine engine, NotifyingConcept notifying) {
        this.engine = engine;
        this.notifying = notifying;
    }

    public static TaggingApp create() {
        FactStore facts = new InMemoryFactStore();
        PostingConcept posting = new PostingConcept(facts.region("Posting"));
        TaggingConcept tagging = new TaggingConcept(facts.region("Tagging"));
        SubscribingConcept subscribing = new SubscribingConcept(facts.region("Subscribing"));
        ProfilingConcept profiling = new ProfilingConcept(facts.region("Profiling"));
        NotifyingConcept notifying = new NotifyingConcept(facts.region("Notifying"));

        List<Concept> concepts = List.of(new WebConcept(), posting, tagging, subscribing, profiling, notifying);
        List<SyncRule> rules = TaggingSyncs.all();
        SyncEngine engine = new SyncEngine(facts, concepts, rules);
        return new TaggingApp(engine, notifying);
    }

    public SyncEngine engine() {
        return engine;
    }

    public Map<String, Object> publish(String author, String content) {
        return engine.run("Web", "request", Map.of("route", "publish", "author", author, "content", content));
    }

    public Map<String, Object> tag(String postId, String tag) {
        return engine.run("Web", "request", Map.of("route", "tag", "postId", postId, "tag", tag));
    }

    public Map<String, Object> subscribe(String userId, String tag) {
        return engine.run("Web", "request", Map.of("route", "subscribe", "userId", userId, "tag", tag));
    }

    public Map<String, Object> setBio(String userId, String bio) {
        return engine.run("Web", "request", Map.of("route", "set-bio", "userId", userId, "bio", bio));
    }

    public Map<String, Object> profile(String userId) {
        return engine.run("Web", "request", Map.of("route", "profile", "userId", userId));
    }

    public Map<String, Object> listTags(String postId) {
        return engine.run("Web", "request", Map.of("route", "list-tags", "postId", postId));
    }

    public List<String> notificationsFor(String userId) {
        return notifying.notificationsFor(userId);
    }
}
