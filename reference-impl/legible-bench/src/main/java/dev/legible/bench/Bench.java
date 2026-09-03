package dev.legible.bench;

import dev.legible.example.login.LoginApp;

import java.util.Map;

/** Sequential throughput probe for the fire-after-commit engine. */
public final class Bench {

    public static void main(String[] args) {
        LoginApp app = LoginApp.create();
        app.seedUser("alice", "secret");

        // warmup
        for (int i = 0; i < 5_000; i++) {
            app.login("alice", "secret");
        }

        int n = 100_000;
        long start = System.nanoTime();
        int ok = 0;
        for (int i = 0; i < n; i++) {
            Map<String, Object> r = app.login("alice", "secret");
            if (r != null && Integer.valueOf(200).equals(r.get("status"))) ok++;
        }
        long end = System.nanoTime();
        double seconds = (end - start) / 1e9;
        double perRequestUs = (end - start) / 1e3 / n;

        System.out.printf("completed %d/%d logins in %.3f s%n", ok, n, seconds);
        System.out.printf("throughput: %.0f ops/s, latency: %.2f us/request%n",
                n / seconds, perRequestUs);
        System.out.printf("in-flight flows after run: %d, archived buffer: %d%n",
                app.engine().inFlight().size(),
                app.engine().archiver().buffer().recent().size());
    }
}
