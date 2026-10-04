package dev.legible.engine;

/**
 * Storage-agnostic fact store. Concepts and the engine talk to this, never to a
 * specific database. The paper's "facts → relations" are realized here; profiles
 * supply an in-memory, SQL, or triplestore implementation.
 */
public interface FactStore {

    /** The named persistence region for {@code concept} (R2). */
    Region region(String concept);

    /**
     * The region for {@code concept}, or {@code null} when the concept owns no
     * region (a stateless/bootstrap concept such as {@code Web}). Callers that
     * can proceed without a region — notably the engine's transactional-write
     * wrapper — use this instead of {@link #region(String)}.
     */
    default Region maybeRegion(String concept) {
        return region(concept);
    }
}
