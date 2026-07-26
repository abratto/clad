package com.example.app.engine.predicate;

import org.apache.jena.query.Dataset;
import org.apache.jena.query.ReadWrite;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Manages Jena transactional boundaries for predicate-based syncs.
 *
 * <p>In the predicate model, a concept's completion and all matching sync
 * invocations must commit atomically — either both graphs see the update or
 * neither does. This class wraps Jena's {@link Dataset#begin(ReadWrite)},
 * commit, and abort to ensure that invariant.
 *
 * <p>The current reference engine commits each action independently
 * (no cross-concept transaction). This class is the minimal addition
 * needed to make concept+synchronization transitions atomic.
 */
public class TransactionManager {

    private static final Logger LOG = LoggerFactory.getLogger(TransactionManager.class);

    private final Dataset dataset;

    public TransactionManager(Dataset dataset) {
        this.dataset = dataset;
    }

    /** Begin a WRITE transaction on the dataset. */
    public void begin() {
        if (dataset.isInTransaction()) {
            LOG.debug("already in transaction — nested begin is a no-op");
            return;
        }
        dataset.begin(ReadWrite.WRITE);
    }

    /** Commit the current transaction. */
    public void commit() {
        if (!dataset.isInTransaction()) {
            LOG.warn("commit called outside transaction");
            return;
        }
        dataset.commit();
        if (dataset.isInTransaction()) {
            dataset.end();
        }
    }

    /** Abort (rollback) the current transaction. */
    public void abort() {
        if (!dataset.isInTransaction()) {
            LOG.warn("abort called outside transaction");
            return;
        }
        dataset.abort();
        if (dataset.isInTransaction()) {
            dataset.end();
        }
    }
}
