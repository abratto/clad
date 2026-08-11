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
import java.util.Map;
import java.util.Properties;

/**
 * Provides action-log storage, configuring the backend from
 * {@code clad.properties}. Local backends expose a Jena {@link Dataset}; the
 * remote Fuseki backend exposes only an {@link ActionLog} backed by HTTP.
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

    private final Properties props;
    private final Map<String, String> environment;
    private final String type;

    public CladDatasetFactory() {
        this(readCladProperties(), System.getenv());
    }

    CladDatasetFactory(Properties props, Map<String, String> environment) {
        this.props = props;
        this.environment = environment;
        this.type = resolve("engine.dataset.type", "ENGINE_DATASET_TYPE", DEFAULT_TYPE);
    }

    @Singleton
    public Dataset dataset() {
        if ("tdb2".equalsIgnoreCase(type)) return connectTdb2();
        if ("tdb2mem".equalsIgnoreCase(type)) return TDB2Factory.createDataset();
        if ("fuseki-embedded".equalsIgnoreCase(type)) return fusekiEmbedded();
        if ("tmemory".equalsIgnoreCase(type)) return DatasetFactory.createTxnMem();
        if ("fuseki".equalsIgnoreCase(type)) throw new IllegalStateException(
                "fuseki backend provides remote ActionLog storage, not a local Dataset");
        throw new IllegalStateException("unsupported engine.dataset.type: " + type);
    }

    /**
     * Provides the {@link ActionLog} bean. When {@code fuseki} backend is
     * selected, wraps a remote SPARQL endpoint via {@link RemoteStorage}.
     * Otherwise, a locally configured Dataset is used.
     */
    @Singleton
    @Primary
    public ActionLog actionLog() {
        if ("fuseki-split".equalsIgnoreCase(type)) {
            return fusekiSplitStorage();
        }
        if ("fuseki".equalsIgnoreCase(type)) {
            return fusekiStorage();
        }
        return new ActionLog(dataset());
    }

    private ActionLog fusekiStorage() {
        String queryEndpoint = resolve("engine.dataset.fuseki.query",
                "CLAD_FUSEKI_QUERY",
                resolve("engine.dataset.fuseki.endpoint", "CLAD_FUSEKI_ENDPOINT", ""));
        String updateEndpoint = resolve("engine.dataset.fuseki.update",
                "CLAD_FUSEKI_UPDATE",
                queryEndpoint);
        if (queryEndpoint.isBlank()) throw new IllegalStateException(
                "engine.dataset.fuseki.endpoint or CLAD_FUSEKI_QUERY required for fuseki backend");
        return buildRemoteActionLog(queryEndpoint, updateEndpoint);
    }

    private ActionLog fusekiSplitStorage() {
        String queryEndpoint = resolve("engine.dataset.fuseki.query",
                "CLAD_FUSEKI_QUERY",
                resolve("engine.dataset.fuseki.endpoint", "CLAD_FUSEKI_ENDPOINT", ""));
        String updateEndpoint = resolve("engine.dataset.fuseki.update",
                "CLAD_FUSEKI_UPDATE",
                queryEndpoint);
        if (queryEndpoint.isBlank()) throw new IllegalStateException(
                "engine.dataset.fuseki.endpoint or CLAD_FUSEKI_QUERY required");

        // Action log → in-memory (bounded, fast, reclaimed on DELETE)
        LocalStorage actionLogStorage = new LocalStorage(DatasetFactory.createTxnMem());
        actionLogStorage.setArchiveEnabled(false);

        // Business graphs → remote Fuseki (durable, bounded)
        RemoteStorage businessStorage = buildRemote(queryEndpoint, updateEndpoint);

        // Create ActionLog first, then wrap with archiver-enabled SplitStorage
        ActionLog log = new ActionLog(new SplitStorage(actionLogStorage, businessStorage));

        // Wire FlowArchiver — reads triples from log, flushes to JSON logger
        if ("true".equals(resolve("engine.archive.log.enabled",
                "CLAD_ARCHIVE_LOG_ENABLED", "false"))) {
            FlowArchiveBuffer buffer = archiveBuffer();
            FlowArchiver archiver = new FlowArchiver(log, buffer);
            ((SplitStorage) log.storage()).setArchiver(archiver);
        }

        return log;
    }

    @Singleton
    FlowArchiveBuffer archiveBuffer() {
        int maxSize = Integer.parseInt(resolve("engine.archive.buffer.size",
                "CLAD_ARCHIVE_BUFFER_SIZE", "100"));
        return new FlowArchiveBuffer(maxSize);
    }

    private ActionLog buildRemoteActionLog(String queryEndpoint, String updateEndpoint) {
        return new ActionLog(buildRemote(queryEndpoint, updateEndpoint));
    }

    private RemoteStorage buildRemote(String queryEndpoint, String updateEndpoint) {
        String username = resolve("engine.dataset.fuseki.username", "CLAD_FUSEKI_USERNAME", "");
        String password = resolve("engine.dataset.fuseki.password", "CLAD_FUSEKI_PASSWORD", "");
        if (username.isBlank() != password.isBlank()) throw new IllegalStateException(
                "engine.dataset.fuseki.username and engine.dataset.fuseki.password must both be set");
        return username.isBlank() && password.isBlank()
            ? new RemoteStorage(queryEndpoint, updateEndpoint)
            : new RemoteStorage(queryEndpoint, updateEndpoint, username, password);
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
        String dir = resolve("engine.dataset.tdb2.dir", "ENGINE_DATASET_TDB2_DIR", DEFAULT_TDB2_DIR);
        try { Files.createDirectories(Path.of(dir)); }
        catch (Exception e) { throw new RuntimeException("cannot create TDB2 dir: " + dir, e); }
        return dir;
    }

    private String resolve(String propertyName, String environmentName, String defaultValue) {
        String systemValue = System.getProperty(propertyName);
        if (systemValue != null) return systemValue;
        String environmentValue = environment.get(environmentName);
        if (environmentValue != null) return environmentValue;
        return props.getProperty(propertyName, defaultValue);
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
