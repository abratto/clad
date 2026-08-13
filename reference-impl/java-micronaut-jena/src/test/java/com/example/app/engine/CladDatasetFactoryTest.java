package com.example.app.engine;

import org.junit.jupiter.api.Test;

import java.util.Map;
import java.util.Properties;

import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;

class CladDatasetFactoryTest {

    @Test
    void composeStyleEnvironmentSelectsRemoteFusekiBusinessBackend() {
        CladDatasetFactory factory = new CladDatasetFactory(new Properties(), Map.of(
                "ENGINE_DATASET_TYPE", "fuseki",
                "CLAD_FUSEKI_ENDPOINT", "http://fuseki:3030/clad/update"));

        ActionLog log = factory.actionLog(new DevNullSink(), new FlowArchiveBuffer());
        assertInstanceOf(SplitStorage.class, log.storage());
        assertInstanceOf(RemoteStorage.class,
                ((SplitStorage) log.storage()).businessBackend());
    }

    @Test
    void remoteBackendStillExposesInMemoryActionLogDataset() {
        CladDatasetFactory factory = new CladDatasetFactory(new Properties(), Map.of(
                "ENGINE_DATASET_TYPE", "fuseki",
                "CLAD_FUSEKI_ENDPOINT", "http://fuseki:3030/clad/update"));

        // The action log is always in-memory — the Dataset is the TxnMem
        // action log, not the remote Fuseki store.
        assertInstanceOf(org.apache.jena.query.Dataset.class,
                factory.actionLog(new DevNullSink(), new FlowArchiveBuffer()).dataset());
    }

    @Test
    void remoteBackendWithoutEndpointFailsClosed() {
        CladDatasetFactory factory = new CladDatasetFactory(new Properties(), Map.of(
                "ENGINE_DATASET_TYPE", "fuseki"));

        assertThrows(IllegalStateException.class,
                () -> factory.actionLog(new DevNullSink(), new FlowArchiveBuffer()));
    }

    @Test
    void partialRemoteCredentialsFailClosed() {
        CladDatasetFactory factory = new CladDatasetFactory(new Properties(), Map.of(
                "ENGINE_DATASET_TYPE", "fuseki",
                "CLAD_FUSEKI_ENDPOINT", "http://fuseki:3030/clad/update",
                "CLAD_FUSEKI_USERNAME", "admin"));

        assertThrows(IllegalStateException.class,
                () -> factory.actionLog(new DevNullSink(), new FlowArchiveBuffer()));
    }

    @Test
    void unsupportedBackendTypeFailsClosed() {
        CladDatasetFactory factory = new CladDatasetFactory(new Properties(), Map.of(
                "ENGINE_DATASET_TYPE", "not-a-backend"));

        assertThrows(IllegalStateException.class, factory::dataset);
    }
}
