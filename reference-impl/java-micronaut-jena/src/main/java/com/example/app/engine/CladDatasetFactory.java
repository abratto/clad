package com.example.app.engine;

import io.micronaut.context.annotation.Factory;
import io.micronaut.context.annotation.Primary;
import jakarta.inject.Singleton;
import org.apache.jena.fuseki.main.FusekiServer;
import org.apache.jena.query.Dataset;
import org.apache.jena.query.DatasetFactory;
import org.apache.jena.tdb2.TDB2Factory;

import java.io.FileInputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Properties;

/**
 * Provides the Jena {@link Dataset} bean, configuring the backend from
 * {@code clad.properties}.
 *
 * <p>Supported backends:
 * <ul>
 *   <li>{@code tmemory} (default) — in-memory transactional Dataset,
 *       zero-setup, for development and testing.</li>
 *   <li>{@code tdb2} — persistent TDB2 store via local directory.</li>
 *   <li>{@code tdb2mem} — in-memory TDB2 store (single-writer only).</li>
 *   <li>{@code fuseki-embedded} — TDB2 with embedded Fuseki HTTP server.</li>
 *   <li>{@code fuseki} — remote Fuseki SPARQL endpoint via HTTP.
 *       Set {@code engine.dataset.fuseki.endpoint} to the URL.</li>
 * </ul>
 */
@Factory
public class CladDatasetFactory {

    private static final String DEFAULT_TYPE = "tmemory";
    private static final String DEFAULT_TDB2_DIR = "./clad-tdb2-store";

    private final Properties props = readCladProperties();
    private final String type = System.getProperty("engine.dataset.type",
            props.getProperty("engine.dataset.type", DEFAULT_TYPE));

    @Singleton
    public Dataset dataset() {
        if ("tdb2".equalsIgnoreCase(type)) return connectTdb2();
        if ("tdb2mem".equalsIgnoreCase(type)) return TDB2Factory.createDataset();
        if ("fuseki-embedded".equalsIgnoreCase(type)) return fusekiEmbedded();
        if ("fuseki".equalsIgnoreCase(type)) return DatasetFactory.createTxnMem();  // stub
        return DatasetFactory.createTxnMem();
    }

    /**
     * Provides the {@link ActionLog} bean. When {@code fuseki} backend is
     * selected, wraps a remote SPARQL endpoint via {@link RemoteStorage}.
     * Otherwise, the default {@code ActionLog(Dataset)} constructor is used.
     */
    @Singleton
    @Primary
    public ActionLog actionLog(Dataset dataset) {
        if ("fuseki".equalsIgnoreCase(type)) {
            String endpoint = System.getProperty("engine.dataset.fuseki.endpoint",
                    props.getProperty("engine.dataset.fuseki.endpoint", ""));
            if (endpoint.isBlank()) throw new RuntimeException(
                    "engine.dataset.fuseki.endpoint required for fuseki backend");
            return new ActionLog(new RemoteStorage(endpoint));
        }
        return new ActionLog(dataset);
    }

    private Dataset connectTdb2() {
        String dir = resolveDir();
        return TDB2Factory.connectDataset(dir);
    }

    private Dataset fusekiEmbedded() {
        String dir = resolveDir();
        Dataset ds = TDB2Factory.connectDataset(dir);
        int port = Integer.parseInt(System.getProperty(
                "engine.dataset.fuseki.port", "0"));

        FusekiServer server = FusekiServer.create()
                .port(port)
                .add("/ds", ds.asDatasetGraph(), true)
                .build();
        server.start();
        System.out.println("[clad] fuseki-embedded admin on http://localhost:"
                + server.getPort() + "/ds (store: " + dir + ")");
        return ds;
    }

    private String resolveDir() {
        String dir = System.getProperty("engine.dataset.tdb2.dir",
                props.getProperty("engine.dataset.tdb2.dir", DEFAULT_TDB2_DIR));
        try { Files.createDirectories(Path.of(dir)); }
        catch (Exception e) { throw new RuntimeException("cannot create TDB2 dir: " + dir, e); }
        return dir;
    }

    private static Properties readCladProperties() {
        Properties props = new Properties();
        try (FileInputStream in = new FileInputStream("clad.properties")) {
            props.load(in);
        } catch (Exception ignored) {
        }
        return props;
    }
}
