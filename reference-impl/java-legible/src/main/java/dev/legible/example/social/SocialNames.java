package dev.legible.example.social;

/**
 * Readable relay constants for the social sync rules; concept strings come
 * from the owning concept classes' {@code NAME} constants. Nothing here is
 * logic — see {@code maintenance/sync-dsl-legibility.md}.
 */
public final class SocialNames {

    public static final String POSTING = PostingConcept.NAME;
    public static final String COMMENTING = CommentingConcept.NAME;
    public static final String FOLLOWING = FollowingConcept.NAME;
    public static final String NOTIFYING = NotifyingConcept.NAME;
    public static final String FEED = FeedConcept.NAME;

    private SocialNames() {
    }
}
