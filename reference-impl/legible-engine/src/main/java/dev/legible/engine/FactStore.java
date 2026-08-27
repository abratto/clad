package dev.legible.engine;

/**
 * Storage-agnostic fact store. Concepts and the engine talk to this, never to a
 * specific database. The paper's "facts → relations" are realized here; profiles
 * supply an in-memory, SQL, or triplestore implementation.
 */
public interface FactStore {

    /** The named persistence region for {@code concept} (R2). */
    Region region(String concept);
}
