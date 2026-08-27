package dev.legible.example.tagging;

import dev.legible.engine.Clause;
import dev.legible.engine.Source;
import dev.legible.engine.SyncRule;
import dev.legible.engine.ThenInvocation;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static dev.legible.engine.SyncRule.invoke;
import static dev.legible.engine.SyncRule.lit;
import static dev.legible.engine.SyncRule.ref;

/**
 * The tagging-feature synchronizations. This feature exercises the two matcher
 * constructs login and the social example do not:
 * <ul>
 *   <li>{@code OPTIONAL} — a {@code where} read that may find nothing leaves the
 *       variable unbound instead of dropping the frame
 *       ({@code WhenWebRequestRoutedThenWebRespondForProfile}).</li>
 *   <li>{@code ?_eachthen} aggregation — a fan-out {@code where} is grouped so
 *       {@code then} fires once per post, not once per tag
 *       ({@code WhenWebRequestRoutedThenWebRespondForListTags}).</li>
 * </ul>
 */
public final class TaggingSyncs {

    private TaggingSyncs() {
    }

    public static List<SyncRule> all() {
        return List.of(
                requestToCreatePost(),
                createPostToRespond(),
                requestToTag(),
                tagToRespond(),
                requestToSubscribe(),
                subscribeToRespond(),
                requestToSetBio(),
                requestToProfile(),
                requestToListTags(),
                tagToNotifySubscribers());
    }

    private static SyncRule requestToCreatePost() {
        return SyncRule.of(
                "WhenWebRequestRoutedThenPostingCreatePostForPublish",
                "Web", "request", "routed",
                List.of(
                        new Clause.Bind("?route", new Source.TriggerInput("route")),
                        new Clause.Guard("?route", lit("publish")),
                        new Clause.Bind("?author", new Source.TriggerInput("author")),
                        new Clause.Bind("?content", new Source.TriggerInput("content"))),
                List.of(invoke("Posting", "createPost",
                        Map.of("author", ref("?author"), "content", ref("?content")))));
    }

    private static SyncRule createPostToRespond() {
        return SyncRule.of(
                "WhenPostingCreatePostCreatedThenWebRespondForPublish",
                "Posting", "createPost", "CREATED",
                List.of(new Clause.Bind("?postId", new Source.TriggerField("postId"))),
                List.of(respond(Map.of("postId", ref("?postId")))));
    }

    private static SyncRule requestToTag() {
        return SyncRule.of(
                "WhenWebRequestRoutedThenTaggingTagForTag",
                "Web", "request", "routed",
                List.of(
                        new Clause.Bind("?route", new Source.TriggerInput("route")),
                        new Clause.Guard("?route", lit("tag")),
                        new Clause.Bind("?postId", new Source.TriggerInput("postId")),
                        new Clause.Bind("?tag", new Source.TriggerInput("tag"))),
                List.of(invoke("Tagging", "tag",
                        Map.of("postId", ref("?postId"), "tag", ref("?tag")))));
    }

    private static SyncRule tagToRespond() {
        return SyncRule.of(
                "WhenTaggingTagTaggedThenWebRespondForTag",
                "Tagging", "tag", "TAGGED",
                List.of(
                        new Clause.Bind("?postId", new Source.TriggerField("postId")),
                        new Clause.Bind("?tag", new Source.TriggerField("tag"))),
                List.of(respond(Map.of("postId", ref("?postId"), "tag", ref("?tag")))));
    }

    private static SyncRule requestToSubscribe() {
        return SyncRule.of(
                "WhenWebRequestRoutedThenSubscribingSubscribeForSubscribe",
                "Web", "request", "routed",
                List.of(
                        new Clause.Bind("?route", new Source.TriggerInput("route")),
                        new Clause.Guard("?route", lit("subscribe")),
                        new Clause.Bind("?userId", new Source.TriggerInput("userId")),
                        new Clause.Bind("?tag", new Source.TriggerInput("tag"))),
                List.of(invoke("Subscribing", "subscribe",
                        Map.of("userId", ref("?userId"), "tag", ref("?tag")))));
    }

    private static SyncRule subscribeToRespond() {
        return SyncRule.of(
                "WhenSubscribingSubscribeSubscribedThenWebRespondForSubscribe",
                "Subscribing", "subscribe", "SUBSCRIBED",
                List.of(
                        new Clause.Bind("?userId", new Source.TriggerField("userId")),
                        new Clause.Bind("?tag", new Source.TriggerField("tag"))),
                List.of(respond(Map.of("userId", ref("?userId"), "tag", ref("?tag")))));
    }

    private static SyncRule requestToSetBio() {
        return SyncRule.of(
                "WhenWebRequestRoutedThenProfilingSetBioForSetBio",
                "Web", "request", "routed",
                List.of(
                        new Clause.Bind("?route", new Source.TriggerInput("route")),
                        new Clause.Guard("?route", lit("set-bio")),
                        new Clause.Bind("?userId", new Source.TriggerInput("userId")),
                        new Clause.Bind("?bio", new Source.TriggerInput("bio"))),
                List.of(invoke("Profiling", "setBio",
                        Map.of("userId", ref("?userId"), "bio", ref("?bio")))));
    }

    /**
     * OPTIONAL: read the user's bio, but leave it unbound (rather than failing
     * the sync) when the user has no bio. The profile responds either way.
     */
    private static SyncRule requestToProfile() {
        return SyncRule.of(
                "WhenWebRequestRoutedThenWebRespondForProfile",
                "Web", "request", "routed",
                List.of(
                        new Clause.Bind("?route", new Source.TriggerInput("route")),
                        new Clause.Guard("?route", lit("profile")),
                        new Clause.Bind("?userId", new Source.TriggerInput("userId")),
                        new Clause.OptionalClause(new Clause.Bind("?bio",
                                new Source.StateRead("Profiling", ref("?userId"), "bio")))),
                List.of(respond(Map.of("userId", ref("?userId"), "bio", ref("?bio")))));
    }

    /**
     * ?_eachthen aggregation: read every tag of a post (fan-out to N frames),
     * then group by the post so the response fires once — not once per tag.
     */
    private static SyncRule requestToListTags() {
        return SyncRule.of(
                "WhenWebRequestRoutedThenWebRespondForListTags",
                "Web", "request", "routed",
                List.of(
                        new Clause.Bind("?route", new Source.TriggerInput("route")),
                        new Clause.Guard("?route", lit("list-tags")),
                        new Clause.Bind("?postId", new Source.TriggerInput("postId")),
                        new Clause.Bind("?tag", new Source.StateRead("Tagging", ref("?postId"), "tag"))),
                List.of(respond(Map.of("postId", ref("?postId")))),
                "?postId");
    }

    /** Fan-out: notify every user watching the tag of the newly-tagged post. */
    private static SyncRule tagToNotifySubscribers() {
        return SyncRule.of(
                "WhenTaggingTagTaggedThenNotifyingNotifySubscribersForTag",
                "Tagging", "tag", "TAGGED",
                List.of(
                        new Clause.Bind("?tag", new Source.TriggerField("tag")),
                        new Clause.FanOut("?subscriber", "Subscribing", "watch", ref("?tag"))),
                List.of(invoke("Notifying", "notify",
                        Map.of("userId", ref("?subscriber"), "message", lit("New content tagged")))));
    }

    private static ThenInvocation respond(Map<String, Source> fields) {
        Map<String, Source> args = new LinkedHashMap<>();
        args.put("status", lit(200));
        args.putAll(fields);
        return invoke("Web", "respond", args);
    }
}
