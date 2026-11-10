package dev.legible.engine;

import java.util.Objects;
import java.util.Set;
import java.util.TreeSet;
import java.util.concurrent.locks.ReentrantLock;

/**
 * Striped locks for per-subject concept serialization.
 *
 * <p>A lock is identified by {@code (concept, lockKey)}. Keys are hashed onto a
 * fixed stripe array, so the registry's memory is bounded and does not grow
 * with the number of subjects. Multi-subject actions acquire their distinct
 * stripe indices in ascending order and release them in reverse, which gives a
 * global acquisition order and prevents deadlock.
 */
final class ConceptLocks {

    /** Sentinel key for an action that is concept-wide (no subject declared). */
    private static final Object CONCEPT_WIDE = new Object();

    private final ReentrantLock[] stripes;

    ConceptLocks() {
        this(4096);
    }

    ConceptLocks(int stripeCount) {
        if (stripeCount <= 0) {
            throw new IllegalArgumentException("stripeCount must be positive");
        }
        this.stripes = new ReentrantLock[stripeCount];
        for (int i = 0; i < stripes.length; i++) {
            stripes[i] = new ReentrantLock();
        }
    }

    /**
     * The distinct stripe indices to acquire for one action, in ascending
     * order. An empty or null key set means concept-wide.
     */
    int[] indexes(String concept, Set<Object> keys) {
        if (keys == null || keys.isEmpty()) {
            return new int[] { index(concept, CONCEPT_WIDE) };
        }
        TreeSet<Integer> distinct = new TreeSet<>();
        for (Object key : keys) {
            distinct.add(index(concept, key));
        }
        int[] out = new int[distinct.size()];
        int i = 0;
        for (int stripe : distinct) {
            out[i++] = stripe;
        }
        return out;
    }

    void acquire(int[] indexes) {
        for (int index : indexes) {
            stripes[index].lock();
        }
    }

    void release(int[] indexes) {
        for (int i = indexes.length - 1; i >= 0; i--) {
            stripes[indexes[i]].unlock();
        }
    }

    private int index(String concept, Object key) {
        return Math.floorMod(Objects.hash(concept, key), stripes.length);
    }
}
