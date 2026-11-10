package dev.legible.engine;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class SyncEngineLockTest {

    private static final class ProbeConcept implements Concept {

        private final boolean stateful;
        private final AtomicInteger inFlight = new AtomicInteger();
        private final AtomicInteger maxInFlight = new AtomicInteger();

        private ProbeConcept(boolean stateful) {
            this.stateful = stateful;
        }

        @Override
        public String name() {
            return "Probe";
        }

        @Override
        public boolean stateful() {
            return stateful;
        }

        @Override
        public Object lockKey(String action, Map<String, Object> input) {
            return input.get("key");
        }

        @Override
        public Map<String, Object> execute(String action, Map<String, Object> input) {
            int now = inFlight.incrementAndGet();
            maxInFlight.accumulateAndGet(now, Math::max);
            try {
                Thread.sleep(25);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            } finally {
                inFlight.decrementAndGet();
            }
            return Map.of("outcome", "OK");
        }
    }

    @Test
    void differentKeysRunConcurrently() throws Exception {
        ProbeConcept probe = new ProbeConcept(true);
        SyncEngine engine = new SyncEngine(new InMemoryFactStore(), List.of(probe), List.of());

        runConcurrently(engine, "a", differentStripe("Probe", "a"));

        assertTrue(probe.maxInFlight.get() >= 2,
                "different subjects must overlap");
    }

    @Test
    void sameKeySerializes() throws Exception {
        ProbeConcept probe = new ProbeConcept(true);
        SyncEngine engine = new SyncEngine(new InMemoryFactStore(), List.of(probe), List.of());

        runConcurrently(engine, "a", "a");

        assertEquals(1, probe.maxInFlight.get(),
                "the same subject must run one action at a time");
    }

    @Test
    void statelessConceptDoesNotTouchARegion() throws Exception {
        ProbeConcept probe = new ProbeConcept(false);
        FactStore noRegions = new FactStore() {
            @Override
            public Region region(String concept) {
                throw new AssertionError("region lookup for a stateless concept");
            }

            @Override
            public Region maybeRegion(String concept) {
                throw new AssertionError("maybeRegion lookup for a stateless concept");
            }
        };
        SyncEngine engine = new SyncEngine(noRegions, List.of(probe), List.of());

        engine.run("Probe", "act", Map.of("key", "a"));

        assertEquals(1, probe.maxInFlight.get());
    }

    private static void runConcurrently(SyncEngine engine, String firstKey, String secondKey)
            throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(2);
        CountDownLatch go = new CountDownLatch(1);
        Future<?> first = pool.submit(() -> {
            go.await();
            engine.run("Probe", "act", Map.of("key", firstKey));
            return null;
        });
        Future<?> second = pool.submit(() -> {
            go.await();
            engine.run("Probe", "act", Map.of("key", secondKey));
            return null;
        });
        go.countDown();
        first.get(2, TimeUnit.SECONDS);
        second.get(2, TimeUnit.SECONDS);
        pool.shutdown();
    }

    private static String differentStripe(String concept, String base) {
        ConceptLocks locks = new ConceptLocks(4096);
        int baseIndex = locks.indexes(concept, Set.of(base))[0];
        for (int i = 0; i < 10_000; i++) {
            String candidate = base + "-" + i;
            if (locks.indexes(concept, Set.of(candidate))[0] != baseIndex) {
                return candidate;
            }
        }
        throw new IllegalStateException("no different stripe found");
    }
}
