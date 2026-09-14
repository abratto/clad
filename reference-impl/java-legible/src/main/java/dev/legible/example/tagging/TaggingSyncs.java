package dev.legible.example.tagging;

import dev.legible.engine.SyncRule;

import java.util.List;
import java.util.Map;

import static dev.legible.engine.Dsl.args;
import static dev.legible.engine.Dsl.bind;
import static dev.legible.engine.Dsl.fanOut;
import static dev.legible.engine.Dsl.invoke;
import static dev.legible.engine.Dsl.lit;
import static dev.legible.engine.Dsl.optional;
import static dev.legible.engine.Dsl.ref;
import static dev.legible.engine.Dsl.rule;
import static dev.legible.engine.Dsl.stateRead;
import static dev.legible.engine.Dsl.triggerField;
import static dev.legible.engine.Dsl.triggerInput;
import static dev.legible.example.tagging.ProfilingConcept.SET_BIO;
import static dev.legible.example.tagging.TaggingNames.PROFILING;
import static dev.legible.example.tagging.TaggingNames.SUBSCRIBING;
import static dev.legible.example.tagging.TaggingNames.TAGGING;
import static dev.legible.example.tagging.TaggingNames.POSTING;
import static dev.legible.example.tagging.TaggingNames.NOTIFYING;
import static dev.legible.example.tagging.SubscribingConcept.SUBSCRIBE;
import static dev.legible.example.tagging.TaggingConcept.TAG;
import dev.legible.example.login.WebConcept;
import static dev.legible.example.social.PostingConcept.CREATE_POST;
import static dev.legible.example.social.NotifyingConcept.NOTIFY;

/**
 * The tagging-feature synchronizations, hand-written against the fluent DSL
 * (see {@code maintenance/sync-dsl-legibility.md}). Names follow the
 * effect-first grammar:
 * {@code <TargetConcept><TargetAction>[For<Scope>]When<TriggerConcept><TriggerAction><TriggerCompletion>}.
 * This feature exercises the three richer where constructs login does not:
 * <ul>
 *   <li>{@code optional(...)} — a read that may find nothing leaves the
 *       variable unbound instead of dropping the frame.</li>
 *   <li>{@code groupBy(...)} — a fan-out {@code where} grouped so {@code then}
 *       fires once per post, not once per tag.</li>
 *   <li>{@code fanOut(...)} — notify every subscriber of a tag, one
 *       invocation per matched subject.</li>
 * </ul>
 */
public final class TaggingSyncs {

    private TaggingSyncs() {
    }

    public static List<SyncRule> all() {
        return List.of(
                postingCreatePostForPublishWhenWebRequestRouted(),
                webRespondForPublishWhenPostingCreatePostCreated(),
                taggingTagForTagWhenWebRequestRouted(),
                webRespondForTagWhenTaggingTagTagged(),
                subscribingSubscribeForSubscribeWhenWebRequestRouted(),
                webRespondForSubscribeWhenSubscribingSubscribeSubscribed(),
                profilingSetBioForSetBioWhenWebRequestRouted(),
                webRespondForProfileWhenWebRequestRouted(),
                webRespondForListTagsWhenWebRequestRouted(),
                notifyingNotifyForTagWhenTaggingTagTagged());
    }

    private static SyncRule postingCreatePostForPublishWhenWebRequestRouted() {
        return rule("PostingCreatePostForPublishWhenWebRequestRouted")
            .when(WebConcept.NAME, WebConcept.REQUEST, "routed")
            .matching(Map.of("route", "publish"))
            .where(bind("?author", triggerInput("author")),
                   bind("?content", triggerInput("content")))
            .then(invoke(POSTING, CREATE_POST,
                    args("author", ref("?author"), "content", ref("?content"))))
            .build();
    }

    private static SyncRule webRespondForPublishWhenPostingCreatePostCreated() {
        return rule("WebRespondForPublishWhenPostingCreatePostCreated")
            .when(POSTING, CREATE_POST, "CREATED")
            .where(bind("?postId", triggerField("postId")))
            .then(invoke(WebConcept.NAME, WebConcept.RESPOND,
                    args("status", lit(200), "postId", ref("?postId"))))
            .build();
    }

    private static SyncRule taggingTagForTagWhenWebRequestRouted() {
        return rule("TaggingTagForTagWhenWebRequestRouted")
            .when(WebConcept.NAME, WebConcept.REQUEST, "routed")
            .matching(Map.of("route", "tag"))
            .where(bind("?postId", triggerInput("postId")),
                   bind("?tag", triggerInput("tag")))
            .then(invoke(TAGGING, TAG,
                    args("postId", ref("?postId"), "tag", ref("?tag"))))
            .build();
    }

    private static SyncRule webRespondForTagWhenTaggingTagTagged() {
        return rule("WebRespondForTagWhenTaggingTagTagged")
            .when(TAGGING, TAG, "TAGGED")
            .where(bind("?postId", triggerField("postId")),
                   bind("?tag", triggerField("tag")))
            .then(invoke(WebConcept.NAME, WebConcept.RESPOND,
                    args("status", lit(200),
                         "postId", ref("?postId"), "tag", ref("?tag"))))
            .build();
    }

    private static SyncRule subscribingSubscribeForSubscribeWhenWebRequestRouted() {
        return rule("SubscribingSubscribeForSubscribeWhenWebRequestRouted")
            .when(WebConcept.NAME, WebConcept.REQUEST, "routed")
            .matching(Map.of("route", "subscribe"))
            .where(bind("?userId", triggerInput("userId")),
                   bind("?tag", triggerInput("tag")))
            .then(invoke(SUBSCRIBING, SUBSCRIBE,
                    args("userId", ref("?userId"), "tag", ref("?tag"))))
            .build();
    }

    private static SyncRule webRespondForSubscribeWhenSubscribingSubscribeSubscribed() {
        return rule("WebRespondForSubscribeWhenSubscribingSubscribeSubscribed")
            .when(SUBSCRIBING, SUBSCRIBE, "SUBSCRIBED")
            .where(bind("?userId", triggerField("userId")),
                   bind("?tag", triggerField("tag")))
            .then(invoke(WebConcept.NAME, WebConcept.RESPOND,
                    args("status", lit(200),
                         "userId", ref("?userId"), "tag", ref("?tag"))))
            .build();
    }

    private static SyncRule profilingSetBioForSetBioWhenWebRequestRouted() {
        return rule("ProfilingSetBioForSetBioWhenWebRequestRouted")
            .when(WebConcept.NAME, WebConcept.REQUEST, "routed")
            .matching(Map.of("route", "set-bio"))
            .where(bind("?userId", triggerInput("userId")),
                   bind("?bio", triggerInput("bio")))
            .then(invoke(PROFILING, SET_BIO,
                    args("userId", ref("?userId"), "bio", ref("?bio"))))
            .build();
    }

    /**
     * OPTIONAL: read the user's bio, but leave it unbound (rather than failing
     * the sync) when the user has no bio. The profile responds either way.
     */
    private static SyncRule webRespondForProfileWhenWebRequestRouted() {
        return rule("WebRespondForProfileWhenWebRequestRouted")
            .when(WebConcept.NAME, WebConcept.REQUEST, "routed")
            .matching(Map.of("route", "profile"))
            .where(bind("?userId", triggerInput("userId")),
                   optional(bind("?bio", stateRead(PROFILING, ref("?userId"), "bio"))))
            .then(invoke(WebConcept.NAME, WebConcept.RESPOND,
                    args("status", lit(200), "userId", ref("?userId"), "bio", ref("?bio"))))
            .build();
    }

    /**
     * {@code ?_eachthen} aggregation: read every tag of a post (fan-out to N
     * frames), then group by the post so the response fires once — not once
     * per tag.
     */
    private static SyncRule webRespondForListTagsWhenWebRequestRouted() {
        return rule("WebRespondForListTagsWhenWebRequestRouted")
            .when(WebConcept.NAME, WebConcept.REQUEST, "routed")
            .matching(Map.of("route", "list-tags"))
            .where(bind("?postId", triggerInput("postId")),
                   bind("?tag", stateRead(TAGGING, ref("?postId"), "tag")))
            .groupBy("?postId")
            .then(invoke(WebConcept.NAME, WebConcept.RESPOND,
                    args("status", lit(200), "postId", ref("?postId"))))
            .build();
    }

    /** Fan-out: notify every user watching the tag of the newly-tagged post. */
    private static SyncRule notifyingNotifyForTagWhenTaggingTagTagged() {
        return rule("NotifyingNotifyForTagWhenTaggingTagTagged")
            .when(TAGGING, TAG, "TAGGED")
            .where(bind("?tag", triggerField("tag")),
                   fanOut("?subscriber", SUBSCRIBING, "watch", ref("?tag")))
            .then(invoke(NOTIFYING, NOTIFY,
                    args("userId", ref("?subscriber"), "message", lit("New content tagged"))))
            .build();
    }
}
