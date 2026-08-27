package dev.clad.engine;

import jakarta.inject.Singleton;

import java.util.Collections;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

/**
 * A semaphore-based notification channel for the dispatch loop, augmented with
 * a concurrent set of triggered concept IRIs.
 *
 * <p>{@link #signal(String)} records which concept just completed an action and
 * releases the semaphore. The concept IRI is a pure scheduling hint — it carries
 * no action name, flow token, or output data, and is used only by
 * {@link SyncDispatcher} to skip syncs whose trigger concept has not fired this
 * tick. The RDF store remains the single source of truth for all coordination
 * (WYSIWID Rule 4 — see {@code methodology/architecture/LEGIBLE.md}).
 *
 * <p><strong>Invariant:</strong> the concept IRI set must never carry per-action
 * routing data (action name, flow token, output values, etc.). The moment it
 * does, it becomes a semantic bus and violates Rule 4.
 */
@Singleton
public class CompletionBus {

    private final Semaphore semaphore = new Semaphore(0);
    private final AtomicReference<Set<String>> triggeredConcepts =
            new AtomicReference<>(ConcurrentHashMap.newKeySet());

    /** Signals that a concept completed an action (scheduling hint only). */
    public void signal(String conceptIri) {
        triggeredConcepts.getAndUpdate(set -> {
            set.add(conceptIri);
            return set;
        });
        semaphore.release();
    }

    /**
     * Blocks until a signal arrives or {@code maxWaitMs} elapses.
     * Guards against stale permits from signals whose concept IRIs were
     * already drained — wakes up, drains permits, but only returns if
     * the set actually has work.
     */
    public void awaitSignal(long maxWaitMs) throws InterruptedException {
        long deadline = System.currentTimeMillis() + maxWaitMs;
        while (System.currentTimeMillis() < deadline) {
            long remaining = deadline - System.currentTimeMillis();
            if (remaining <= 0) break;
            if (semaphore.tryAcquire(remaining, TimeUnit.MILLISECONDS)) {
                semaphore.drainPermits();
                if (!triggeredConcepts.get().isEmpty()) return;
            }
        }
    }

    /**
     * Atomically returns the set of concept IRIs that have signalled since the
     * last drain, and clears the accumulator.
     */
    public Set<String> drainTriggeredConcepts() {
        Set<String> snapshot = triggeredConcepts.getAndSet(ConcurrentHashMap.newKeySet());
        if (snapshot.isEmpty()) {
            return Collections.emptySet();
        }
        return Collections.unmodifiableSet(snapshot);
    }
}
