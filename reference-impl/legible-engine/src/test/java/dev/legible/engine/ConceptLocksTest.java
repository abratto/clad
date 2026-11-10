package dev.legible.engine;

import org.junit.jupiter.api.Test;

import java.util.Set;
import java.util.concurrent.Callable;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ConceptLocksTest {

    @Test
    void sameKeySerializes() throws Exception {
        ConceptLocks locks = new ConceptLocks(64);
        int[] held = locks.indexes("C", Set.of("a"));
        locks.acquire(held);

        CountDownLatch started = new CountDownLatch(1);
        CountDownLatch acquired = new CountDownLatch(1);
        Thread thread = new Thread(() -> {
            started.countDown();
            locks.acquire(locks.indexes("C", Set.of("a")));
            acquired.countDown();
        });
        thread.start();
        assertTrue(started.await(1, TimeUnit.SECONDS));
        assertFalse(acquired.await(100, TimeUnit.MILLISECONDS),
                "the same key must wait for the held lock");

        locks.release(held);
        assertTrue(acquired.await(2, TimeUnit.SECONDS));
        thread.join();
    }

    @Test
    void differentKeysOverlap() throws Exception {
        ConceptLocks locks = new ConceptLocks(4096);
        int[] held = locks.indexes("C", Set.of("a"));
        locks.acquire(held);

        CountDownLatch acquired = new CountDownLatch(1);
        Thread thread = new Thread(() -> {
            locks.acquire(locks.indexes("C", Set.of(differentStripe("C", "a"))));
            acquired.countDown();
        });
        thread.start();
        assertTrue(acquired.await(2, TimeUnit.SECONDS),
                "a different key must acquire while another is held");

        locks.release(held);
        thread.join();
    }

    @Test
    void multiKeyAcquisitionIsOrderedAndDoesNotDeadlock() throws Exception {
        ConceptLocks locks = new ConceptLocks(4096);
        ExecutorService pool = Executors.newFixedThreadPool(2);
        CountDownLatch go = new CountDownLatch(1);

        Callable<Void> forward = () -> {
            go.await();
            int[] indexes = locks.indexes("C", Set.of("x", "y"));
            locks.acquire(indexes);
            try {
                Thread.sleep(20);
            } finally {
                locks.release(indexes);
            }
            return null;
        };
        Callable<Void> reverse = () -> {
            go.await();
            int[] indexes = locks.indexes("C", Set.of("y", "x"));
            locks.acquire(indexes);
            try {
                Thread.sleep(20);
            } finally {
                locks.release(indexes);
            }
            return null;
        };

        Future<Void> first = pool.submit(forward);
        Future<Void> second = pool.submit(reverse);
        go.countDown();
        first.get(2, TimeUnit.SECONDS);
        second.get(2, TimeUnit.SECONDS);
        pool.shutdown();
    }

    @Test
    void conceptWideKeysAreStable() {
        ConceptLocks locks = new ConceptLocks(64);
        assertArrayEquals(locks.indexes("C", Set.of()), locks.indexes("C", Set.of()));
        assertArrayEquals(locks.indexes("C", null), locks.indexes("C", Set.of()));
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
