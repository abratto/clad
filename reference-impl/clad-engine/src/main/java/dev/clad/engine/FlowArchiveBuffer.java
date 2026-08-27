package dev.clad.engine;

import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.riot.Lang;
import org.apache.jena.riot.RDFDataMgr;

import java.io.StringReader;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Small in-memory buffer of recently completed flow triples, keyed by
 * flow token. Used by the debug endpoint when completed flows are deleted
 * from the in-memory action log after being flushed to the sink.
 *
 * <p>Bounded to {@code maxSize} entries (default 100). Oldest entry is
 * evicted when the buffer is full. Each entry stores the serialized
 * N-Quads and the archiving timestamp.
 */
public class FlowArchiveBuffer {

    private final int maxSize;
    private final LinkedHashMap<String, ArchiveEntry> buffer;

    public FlowArchiveBuffer() {
        this(100);
    }

    public FlowArchiveBuffer(int maxSize) {
        this.maxSize = maxSize;
        this.buffer = new LinkedHashMap<>(maxSize, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry<String, ArchiveEntry> eldest) {
                return size() > maxSize;
            }
        };
    }

    /**
     * Stores a completed flow's triples before they are deleted.
     */
    public void store(String flowToken, byte[] nquads) {
        synchronized (buffer) {
            buffer.put(flowToken, new ArchiveEntry(Instant.now(), nquads));
        }
    }

    /**
     * Retrieves a completed flow's triples as a Jena Model, or null if
     * the flow is not in the buffer.
     */
    public Model get(String flowToken) {
        ArchiveEntry entry;
        synchronized (buffer) {
            entry = buffer.get(flowToken);
        }
        if (entry == null) return null;
        Model model = ModelFactory.createDefaultModel();
        RDFDataMgr.read(model, new StringReader(new String(entry.nquads)),
                "", Lang.NQ);
        return model;
    }

    /**
     * Lists recently archived flow tokens with timestamps.
     */
    public List<Map.Entry<String, Instant>> list() {
        synchronized (buffer) {
            return buffer.entrySet().stream()
                    .map(e -> Map.entry(e.getKey(), e.getValue().timestamp))
                    .toList();
        }
    }

    public int size() {
        synchronized (buffer) {
            return buffer.size();
        }
    }

    static class ArchiveEntry {
        final Instant timestamp;
        final byte[] nquads;
        ArchiveEntry(Instant timestamp, byte[] nquads) {
            this.timestamp = timestamp;
            this.nquads = nquads;
        }
    }
}
