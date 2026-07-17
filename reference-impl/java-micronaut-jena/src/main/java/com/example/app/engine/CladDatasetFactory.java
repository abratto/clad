package com.example.app.engine;

import io.micronaut.context.annotation.Factory;
import jakarta.inject.Singleton;
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
 *   <li>{@code tdb2} — persistent MVCC store with concurrent read/write,
 *       for production deployments.</li>
 * </ul>
 *
 * <p>The TDB2 data directory is read from {@code engine.dataset.tdb2.dir}
 * (default: {@code ./clad-tdb2-store}).
 */
@Factory
public class CladDatasetFactory {

    private static final String DEFAULT_TYPE = "tmemory";
    private static final String DEFAULT_TDB2_DIR = "./clad-tdb2-store";

    @Singleton
    public Dataset dataset() {
        Properties props = readCladProperties();
        // System properties override clad.properties for test/docker configs
        String type = System.getProperty("engine.dataset.type",
                props.getProperty("engine.dataset.type", DEFAULT_TYPE));
        if ("tdb2".equalsIgnoreCase(type)) {
            String dir = System.getProperty("engine.dataset.tdb2.dir",
                    props.getProperty("engine.dataset.tdb2.dir", DEFAULT_TDB2_DIR));
            try {
                Files.createDirectories(Path.of(dir));
            } catch (Exception e) {
                throw new RuntimeException("cannot create TDB2 directory: " + dir, e);
            }
            return TDB2Factory.connectDataset(dir);
        }
        if ("tdb2mem".equalsIgnoreCase(type)) {
            return TDB2Factory.createDataset();
        }
        return DatasetFactory.createTxnMem();
    }

    private static Properties readCladProperties() {
        Properties props = new Properties();
        try (FileInputStream in = new FileInputStream("clad.properties")) {
            props.load(in);
        } catch (Exception ignored) {
            // Use defaults
        }
        return props;
    }
}
