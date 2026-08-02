package com.example.app.engine;

import org.junit.jupiter.api.Test;

import java.util.Map;
import java.util.Properties;

import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;

class CladDatasetFactoryTest {

    @Test
    void composeStyleEnvironmentSelectsRemoteFusekiStorage() {
        CladDatasetFactory factory = new CladDatasetFactory(new Properties(), Map.of(
                "ENGINE_DATASET_TYPE", "fuseki",
                "CLAD_FUSEKI_ENDPOINT", "http://fuseki:3030/clad/update"));

        assertInstanceOf(RemoteStorage.class, factory.actionLog().storage());
    }

    @Test
    void remoteBackendCannotExposeAnUnconnectedLocalDataset() {
        CladDatasetFactory factory = new CladDatasetFactory(new Properties(), Map.of(
                "ENGINE_DATASET_TYPE", "fuseki",
                "CLAD_FUSEKI_ENDPOINT", "http://fuseki:3030/clad/update"));

        assertThrows(IllegalStateException.class, factory::dataset);
    }

    @Test
    void remoteBackendWithoutEndpointFailsClosed() {
        CladDatasetFactory factory = new CladDatasetFactory(new Properties(), Map.of(
                "ENGINE_DATASET_TYPE", "fuseki"));

        assertThrows(IllegalStateException.class, factory::actionLog);
    }

    @Test
    void partialRemoteCredentialsFailClosed() {
        CladDatasetFactory factory = new CladDatasetFactory(new Properties(), Map.of(
                "ENGINE_DATASET_TYPE", "fuseki",
                "CLAD_FUSEKI_ENDPOINT", "http://fuseki:3030/clad/update",
                "CLAD_FUSEKI_USERNAME", "admin"));

            assertThrows(IllegalStateException.class, factory::actionLog);
            }

            @Test
            void unsupportedBackendTypeFailsClosed() {
            CladDatasetFactory factory = new CladDatasetFactory(new Properties(), Map.of(
                "ENGINE_DATASET_TYPE", "not-a-backend"));

            assertThrows(IllegalStateException.class, factory::dataset);
    }
}