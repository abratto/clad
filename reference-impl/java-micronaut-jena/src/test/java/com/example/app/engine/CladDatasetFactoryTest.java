package com.example.app.engine;

import org.apache.jena.query.Dataset;
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

        Dataset dataset = factory.dataset();

        assertInstanceOf(RemoteStorage.class, factory.actionLog(dataset).storage());
    }

    @Test
    void remoteBackendWithoutEndpointFailsClosed() {
        CladDatasetFactory factory = new CladDatasetFactory(new Properties(), Map.of(
                "ENGINE_DATASET_TYPE", "fuseki"));
        Dataset dataset = factory.dataset();

        assertThrows(IllegalStateException.class, () -> factory.actionLog(dataset));
    }

    @Test
    void partialRemoteCredentialsFailClosed() {
        CladDatasetFactory factory = new CladDatasetFactory(new Properties(), Map.of(
                "ENGINE_DATASET_TYPE", "fuseki",
                "CLAD_FUSEKI_ENDPOINT", "http://fuseki:3030/clad/update",
                "CLAD_FUSEKI_USERNAME", "admin"));
        Dataset dataset = factory.dataset();

        assertThrows(IllegalStateException.class, () -> factory.actionLog(dataset));
    }
}