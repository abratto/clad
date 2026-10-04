package dev.legible.engine;

/**
 * Optional capability on a {@link Region}: buffer the writes made during one
 * concept action and flush them as a single multi-column statement per
 * individual. This is what lets a relational realisation honour Rmap's
 * <strong>mandatory → NOT NULL</strong> rule: the SPI writes facts one at a
 * time, so a row's mandatory columns arrive across several calls — flushing the
 * buffered column-set in one statement satisfies {@code NOT NULL} atomically.
 * It also reduces N round-trips to one upsert per individual.
 *
 * <p>The engine calls {@link #beginAction()} immediately before a concept
 * action and {@link #flushAction()} (or {@link #abortAction()} on failure)
 * immediately after, when the region implements this interface. Regions that do
 * not (the in-memory store, the generic fact store) are unaffected.
 *
 * <p>Only single-valued facts are coalesced into the row; a multi-valued fact
 * (a predicate written with more than one value) is realised by Rmap as a child
 * table and flushed as separate rows, so buffering never merges distinct values.
 */
public interface TransactionalRegion extends Region {

    /** Begin buffering writes for the next concept action. */
    void beginAction();

    /** Commit the buffered writes for this action as one statement per individual. */
    void flushAction();

    /** Discard the buffered writes for this action (the action failed). */
    void abortAction();
}
