package dev.legible.example.social;

import dev.legible.engine.SyncRule;

import java.util.List;
import java.util.Map;

import static dev.legible.engine.Dsl.args;
import static dev.legible.engine.Dsl.bind;
import static dev.legible.engine.Dsl.fanOut;
import static dev.legible.engine.Dsl.invoke;
import static dev.legible.engine.Dsl.lit;
import static dev.legible.engine.Dsl.ref;
import static dev.legible.engine.Dsl.rule;
import static dev.legible.engine.Dsl.stateRead;
import static dev.legible.engine.Dsl.triggerField;
import static dev.legible.engine.Dsl.triggerInput;
import static dev.legible.example.social.CommentingConcept.COMMENT;
import static dev.legible.example.social.SocialNames.POSTING;
import static dev.legible.example.social.SocialNames.COMMENTING;
import static dev.legible.example.social.SocialNames.FOLLOWING;
import static dev.legible.example.social.SocialNames.NOTIFYING;
import static dev.legible.example.social.SocialNames.FEED;
import static dev.legible.example.social.FeedConcept.APPEND;
import static dev.legible.example.social.FollowingConcept.FOLLOW;
import static dev.legible.example.social.NotifyingConcept.NOTIFY;
import static dev.legible.example.social.PostingConcept.CREATE_POST;
import dev.legible.example.login.WebConcept;
public final class SocialSyncs {

    private SocialSyncs() {
    }

    public static List<SyncRule> all() {
        return List.of(
                postingCreatePostForPublishWhenWebRequestRouted(),
                webRespondForPublishWhenPostingCreatePostCreated(),
                commentingCommentForCommentWhenWebRequestRouted(),
                webRespondForCommentWhenCommentingCommentCommented(),
                notifyingAndAppendFeedWhenCommentingCommentCommented(),
                notifyingFollowersWhenCommentingCommentCommented(),
                followingFollowForFollowWhenWebRequestRouted(),
                webRespondForFollowWhenFollowingFollowFollowed());
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

    private static SyncRule commentingCommentForCommentWhenWebRequestRouted() {
        return rule("CommentingCommentForCommentWhenWebRequestRouted")
            .when(WebConcept.NAME, WebConcept.REQUEST, "routed")
            .matching(Map.of("route", "comment"))
            .where(bind("?postId", triggerInput("postId")),
                   bind("?author", triggerInput("author")),
                   bind("?text", triggerInput("text")))
            .then(invoke(COMMENTING, COMMENT,
                    args("postId", ref("?postId"), "author", ref("?author"), "text", ref("?text"))))
            .build();
    }

    private static SyncRule webRespondForCommentWhenCommentingCommentCommented() {
        return rule("WebRespondForCommentWhenCommentingCommentCommented")
            .when(COMMENTING, COMMENT, "COMMENTED")
            .where(bind("?commentId", triggerField("commentId")))
            .then(invoke(WebConcept.NAME, WebConcept.RESPOND,
                    args("status", lit(200), "commentId", ref("?commentId"))))
            .build();
    }

    /**
     * Pattern D + multi-target then: read the post's author from Posting's state,
     * then notify that author AND append the comment to their feed — one sync,
     * two downstream invocations.
     */
    private static SyncRule notifyingAndAppendFeedWhenCommentingCommentCommented() {
        return rule("NotifyingNotifyAndFeedAppendWhenCommentingCommentCommented")
            .when(COMMENTING, COMMENT, "COMMENTED")
            .where(bind("?postId", triggerField("postId")),
                   bind("?commentId", triggerField("commentId")),
                   bind("?postAuthor", stateRead(POSTING, ref("?postId"), "author")))
            .then(invoke(NOTIFYING, NOTIFY,
                    args("userId", ref("?postAuthor"), "message", lit("Your post received a comment"))),
                  invoke(FEED, APPEND,
                    args("userId", ref("?postAuthor"), "itemId", ref("?commentId"))))
            .build();
    }

    /** Fan-out: notify every follower of the comment's author (one frame each). */
    private static SyncRule notifyingFollowersWhenCommentingCommentCommented() {
        return rule("NotifyingNotifyForFollowersWhenCommentingCommentCommented")
            .when(COMMENTING, COMMENT, "COMMENTED")
            .where(bind("?author", triggerField("author")),
                   fanOut("?follower", FOLLOWING, "target", ref("?author")))
            .then(invoke(NOTIFYING, NOTIFY,
                    args("userId", ref("?follower"), "message", lit("Someone you follow commented"))))
            .build();
    }

    private static SyncRule followingFollowForFollowWhenWebRequestRouted() {
        return rule("FollowingFollowForFollowWhenWebRequestRouted")
            .when(WebConcept.NAME, WebConcept.REQUEST, "routed")
            .matching(Map.of("route", "follow"))
            .where(bind("?follower", triggerInput("follower")),
                   bind("?target", triggerInput("target")))
            .then(invoke(FOLLOWING, FOLLOW,
                    args("follower", ref("?follower"), "target", ref("?target"))))
            .build();
    }

    private static SyncRule webRespondForFollowWhenFollowingFollowFollowed() {
        return rule("WebRespondForFollowWhenFollowingFollowFollowed")
            .when(FOLLOWING, FOLLOW, "FOLLOWED")
            .where(bind("?follower", triggerField("follower")))
            .then(invoke(WebConcept.NAME, WebConcept.RESPOND,
                    args("status", lit(200), "followed", ref("?follower"))))
            .build();
    }
}
