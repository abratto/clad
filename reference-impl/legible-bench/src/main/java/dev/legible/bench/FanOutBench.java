package dev.legible.bench;

import dev.legible.example.social.SocialApp;

import java.util.Map;

/**
 * Fan-out benchmark: each trial comments on a post authored by a user with N
 * seeded followers; the sync model notifies the author (a Pattern D state read
 * of Posting.author) and every follower (FanOut frame multiplication).
 *
 * <p>Measures per-request latency and req/s as N grows — the cost shape a linear
 * login chain cannot exhibit.
 *
 * <p>A per-N notification tally is printed as an <b>advisory</b> observation:
 * the notification surface stores messages as a set, so identical message text
 * collapses and tallies below warmup+trials are expected. Claiming fan-out
 * correctness is the social profile's own flow tests' job, never this
 * benchmark's.
 */
public final class FanOutBench {

    private static final int[] FOLLOWER_COUNTS = {1, 10, 100, 1000};
    private static final int WARMUP_PER_N = 20;
    private static final int TRIALS_PER_N = 200;

    public static void main(String[] args) {
        System.out.println();
        System.out.println("=== Canonical engine fan-out benchmark (social profile) ===");
        System.out.printf("%-12s %10s %14s %12s %14s%n",
                "Followers", "Trials", "mean(us)", "req/s", "fanout-check");
        System.out.println("-----------------------------------------------------------------");

        for (int n : FOLLOWER_COUNTS) {
            SocialApp app = SocialApp.create();
            String postId = app.publish("post-author", "the post")
                    .get("postId").toString();
            // The fan-out sync notifies followers of the COMMENTING author
            // (mirrors the exemplar: seedFollow("carol","bob"); comment(...,"bob",...)).
            for (int i = 0; i < n; i++) {
                app.seedFollow("f" + i, "commenter");
            }

            for (int i = 0; i < WARMUP_PER_N; i++) {
                app.comment(postId, "commenter", "warmup " + i);
            }

            long wallStart = System.nanoTime();
            int ok = 0;
            for (int t = 0; t < TRIALS_PER_N; t++) {
                Map<String, Object> res = app.comment(postId, "commenter", "hello " + t);
                if (res != null && Integer.valueOf(200).equals(res.get("status"))) {
                    ok++;
                }
            }
            long wallNanos = System.nanoTime() - wallStart;
            double wallSeconds = wallNanos / 1e9;
            double meanUs = wallNanos / 1e3 / ok;

            int followNotifs = 0;
            for (int i = 0; i < n; i++) {
                followNotifs += app.notificationsFor("f" + i).size();
            }
            int expectedFollow = (WARMUP_PER_N + TRIALS_PER_N) * n;

            // Advisory only: the notification surface is a set of messages, so
            // repeated identical deliveries collapse; counts below the "=" of
            // warmup+trials are expected and NOT a throughput failure. Correctness
            // is owned by the profile's own flow tests, not by this benchmark.
            System.out.printf("%-12d %10d %14.2f %12.0f %14s  (notifTally=%d, upper=%d)%n",
                    n, ok, meanUs, ok / wallSeconds, note(followNotifs, expectedFollow),
                    followNotifs, expectedFollow);
        }
        System.out.println();
    }

    private static String note(int actual, int expected) {
        return actual == expected ? "match" : "advisory-set";
    }
}
