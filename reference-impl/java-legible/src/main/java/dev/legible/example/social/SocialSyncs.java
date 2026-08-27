package dev.legible.example.social;

import dev.legible.engine.Clause;
import dev.legible.engine.Source;
import dev.legible.engine.SyncRule;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static dev.legible.engine.SyncRule.invoke;
import static dev.legible.engine.SyncRule.lit;
import static dev.legible.engine.SyncRule.ref;

/**
 * The social-feature synchronizations. Unlike login (a single linear chain),
 * these exercise the richer parts of the sync model:
 * <ul>
 *   <li>fan-out — one comment notifies every follower (frames).</li>
 *   <li>Pattern D — a sync reads another concept's state
 *       ({@code Posting.author}) in its {@code where} clause.</li>
 *   <li>multiple syncs on one trigger — a comment fires three syncs.</li>
 *   <li>multi-target {@code then} — one sync emits two invocations.</li>
 * </ul>
 */
public final class SocialSyncs {

    private SocialSyncs() {
    }

    public static List<SyncRule> all() {
        return List.of(
                requestToCreatePost(),
                createPostToRespond(),
                requestToComment(),
                commentToRespond(),
                commentToNotifyAuthorAndAppendFeed(),
                commentToNotifyFollowers(),
                requestToFollow(),
                followToRespond());
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

    private static SyncRule requestToComment() {
        return SyncRule.of(
                "WhenWebRequestRoutedThenCommentingCommentForComment",
                "Web", "request", "routed",
                List.of(
                        new Clause.Bind("?route", new Source.TriggerInput("route")),
                        new Clause.Guard("?route", lit("comment")),
                        new Clause.Bind("?postId", new Source.TriggerInput("postId")),
                        new Clause.Bind("?author", new Source.TriggerInput("author")),
                        new Clause.Bind("?text", new Source.TriggerInput("text"))),
                List.of(invoke("Commenting", "comment",
                        Map.of("postId", ref("?postId"), "author", ref("?author"), "text", ref("?text")))));
    }

    private static SyncRule commentToRespond() {
        return SyncRule.of(
                "WhenCommentingCommentCommentedThenWebRespondForComment",
                "Commenting", "comment", "COMMENTED",
                List.of(new Clause.Bind("?commentId", new Source.TriggerField("commentId"))),
                List.of(respond(Map.of("commentId", ref("?commentId")))));
    }

    /**
     * Pattern D + multi-target then: read the post's author from Posting's state,
     * then notify that author AND append the comment to their feed — one sync,
     * two downstream invocations.
     */
    private static SyncRule commentToNotifyAuthorAndAppendFeed() {
        return SyncRule.of(
                "WhenCommentingCommentCommentedThenNotifyAuthorAndAppendFeed",
                "Commenting", "comment", "COMMENTED",
                List.of(
                        new Clause.Bind("?postId", new Source.TriggerField("postId")),
                        new Clause.Bind("?commentId", new Source.TriggerField("commentId")),
                        new Clause.Bind("?postAuthor",
                                new Source.StateRead("Posting", ref("?postId"), "author"))),
                List.of(
                        invoke("Notifying", "notify",
                                Map.of("userId", ref("?postAuthor"), "message", lit("Your post received a comment"))),
                        invoke("Feed", "append",
                                Map.of("userId", ref("?postAuthor"), "itemId", ref("?commentId")))));
    }

    /** Fan-out: notify every follower of the comment's author (one frame each). */
    private static SyncRule commentToNotifyFollowers() {
        return SyncRule.of(
                "WhenCommentingCommentCommentedThenNotifyFollowers",
                "Commenting", "comment", "COMMENTED",
                List.of(
                        new Clause.Bind("?author", new Source.TriggerField("author")),
                        new Clause.FanOut("?follower", "Following", "target", ref("?author"))),
                List.of(invoke("Notifying", "notify",
                        Map.of("userId", ref("?follower"), "message", lit("Someone you follow commented")))));
    }

    private static SyncRule requestToFollow() {
        return SyncRule.of(
                "WhenWebRequestRoutedThenFollowingFollowForFollow",
                "Web", "request", "routed",
                List.of(
                        new Clause.Bind("?route", new Source.TriggerInput("route")),
                        new Clause.Guard("?route", lit("follow")),
                        new Clause.Bind("?follower", new Source.TriggerInput("follower")),
                        new Clause.Bind("?target", new Source.TriggerInput("target"))),
                List.of(invoke("Following", "follow",
                        Map.of("follower", ref("?follower"), "target", ref("?target")))));
    }

    private static SyncRule followToRespond() {
        return SyncRule.of(
                "WhenFollowingFollowFollowedThenWebRespondForFollow",
                "Following", "follow", "FOLLOWED",
                List.of(new Clause.Bind("?follower", new Source.TriggerField("follower"))),
                List.of(respond(Map.of("followed", ref("?follower")))));
    }

    private static dev.legible.engine.ThenInvocation respond(Map<String, Source> fields) {
        Map<String, Source> args = new LinkedHashMap<>();
        args.put("status", lit(200));
        args.putAll(fields);
        return invoke("Web", "respond", args);
    }
}
