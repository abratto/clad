package dev.legible.storage;

import dev.legible.engine.FactStore;

/** {@link JenaFactStore} satisfies the storage contract and runs the login feature. */
class JenaFactStoreTest extends StorageContractTest {

    @Override
    FactStore newStore() {
        return JenaFactStore.inMemory();
    }
}
