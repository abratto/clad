package dev.legible.bench;

import dev.legible.example.login.LoginApp;

import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Per-concept serialization ceiling: all threads hammer the SAME user, so every
 * login serializes on that concept's action lock. Reported as the counterpart
 * to the unique-user sweep in {@link ConcurrencyBench}:
 *
 * <ul>
 *   <li><b>same user</b> — every run() contends on the same concept state
 *       machine; max sustainable actions/sec ≈ 1 / avg action latency.</li>
 *   <li><b>unique user</b> ({@link ConcurrencyBench}) — per-concept
 *       serialization shards across individuals and scales with cores.</li>
 * </ul>
 */
public final class SerializationBench {

    private static final int WARMUP_REQUESTS = 200;
    private static final int[] CONCURRENCY_LEVELS = {1, 8, 32, 64};
    private static final int REQUESTS_PER_THREAD = 200;

    public static void main(String[] args) throws Exception {
        LoginApp app = LoginApp.create();
        app.seedUser("hot-user", "hot-pass");

        for (int i = 0; i < WARMUP_REQUESTS; i++) {
            app.login("hot-user", "hot-pass");
        }

        System.out.println();
        System.out.println("=== Canonical engine serialization-ceiling benchmark ===");
        System.out.println("Same user for every request (per-concept hot contention).");
        System.out.println("Per-thread requests: " + REQUESTS_PER_THREAD);
        System.out.printf("%-12s %10s %14s %12s%n",
                "Concurrency", "Trials", "mean(us)", "req/s");
        System.out.println("-------------------------------------------------");

        for (int concurrency : CONCURRENCY_LEVELS) {
            run(app, concurrency);
        }
        System.out.println();
        System.out.println("(unique-user scaling for comparison = ConcurrencyBench)");
        System.out.println();
    }

    private static void run(LoginApp app, int numThreads) throws Exception {
        CountDownLatch startLatch = new CountDownLatch(1);
        CountDownLatch doneLatch = new CountDownLatch(numThreads);
        AtomicInteger ok = new AtomicInteger();

        for (int t = 0; t < numThreads; t++) {
            Thread thread = new Thread(() -> {
                try {
                    startLatch.await();
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    return;
                }
                for (int i = 0; i < REQUESTS_PER_THREAD; i++) {
                    try {
                        Map<String, Object> r = app.login("hot-user", "hot-pass");
                        if (r != null && Integer.valueOf(200).equals(r.get("status"))) {
                            ok.incrementAndGet();
                        }
                    } catch (RuntimeException e) {
                        // benchmarks never fail silently on errors — count them
                        // via a plain static int below for reporting
                        errors.incrementAndGet();
                    }
                }
                doneLatch.countDown();
            }, "hot-" + t);
            thread.start();
        }

        long wallStart = System.nanoTime();
        startLatch.countDown();
        doneLatch.await();
        long wallNanos = System.nanoTime() - wallStart;
        double wallSeconds = wallNanos / 1e9;

        System.out.printf("sanity: errors=%d%n", errors.get());
        System.out.printf("%-12d %10d %14.2f %12.0f%n",
                numThreads, ok.get(),
                wallNanos / 1e3 / Math.max(1, ok.get()),
                ok.get() / wallSeconds);
    }

    private static final AtomicInteger errors = new AtomicInteger();
}
