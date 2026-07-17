package com.example.app.engine;

import io.micronaut.context.annotation.Factory;
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
 *   <li>{@code fuseki-embedded} — TDB2 with embedded Fuseki HTTP admin
 *       server on a random port. Jetty 12 runs alongside Micronaut's
 *       Netty with an explicit pinned dependency.</li>
 * </ul>
 *
 * <p>Planned:
 * <ul>
 *   <li>{@code fuseki} — remote endpoint via SPARQL Graph Store Protocol.
 *       Needs a {@code RemoteDatasetGraph} adapter.</li>
 * </ul>
 */
@Factory
public class CladDatasetFactory {

    private static final String DEFAULT_TYPE = "tmemory";
    private static final String DEFAULT_TDB2_DIR = "./clad-tdb2-store";

    @Singleton
    public Dataset dataset() {
        Properties props = readCladProperties();
        String type = System.getProperty("engine.dataset.type",
                props.getProperty("engine.dataset.type", DEFAULT_TYPE));

        if ("tdb2".equalsIgnoreCase(type)) {
            return connectTdb2(props);
        }
        if ("tdb2mem".equalsIgnoreCase(type)) {
            return TDB2Factory.createDataset();
        }
        if ("fuseki-embedded".equalsIgnoreCase(type)) {
            return fusekiEmbedded(props);
        }
        return DatasetFactory.createTxnMem();
    }

    private Dataset connectTdb2(Properties props) {
        String dir = resolveDir(props);
        return TDB2Factory.connectDataset(dir);
    }

    private String resolveDir(Properties props) {
        String dir = System.getProperty("engine.dataset.tdb2.dir",
                props.getProperty("engine.dataset.tdb2.dir", DEFAULT_TDB2_DIR));
        try {
            Files.createDirectories(Path.of(dir));
        } catch (Exception e) {
            throw new RuntimeException("cannot create TDB2 directory: " + dir, e);
        }
        return dir;
    }

    private Dataset fusekiEmbedded(Properties props) {
        String dir = resolveDir(props);
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

    private static Properties readCladProperties() {
        Properties props = new Properties();
        try (FileInputStream in = new FileInputStream("clad.properties")) {
            props.load(in);
        } catch (Exception ignored) {
        }
        return props;
    }
}
