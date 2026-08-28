package dev.legible.storage;

import dev.legible.engine.Fact;
import dev.legible.engine.FactStore;
import dev.legible.engine.Region;
import org.apache.jena.query.Dataset;
import org.apache.jena.query.DatasetFactory;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.Property;
import org.apache.jena.rdf.model.RDFNode;
import org.apache.jena.rdf.model.Resource;
import org.apache.jena.rdf.model.ResourceFactory;
import org.apache.jena.rdf.model.Statement;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * A {@link FactStore} backed by an Apache Jena {@link Dataset}, with one named
 * graph per concept ({@code concept:<name>}). Facts are triples
 * {@code <subject> <predicate> "value"} inside that graph.
 *
 * <p>This is the triplestore profile implementation of the fire-after-commit
 * engine's storage SPI — the same {@code Concept}/{@code SyncRule} code runs
 * against it unmodified.
 */
public final class JenaFactStore implements FactStore {

    private static final String NS = "https://clad.dev/fact/";

    private final Dataset dataset;
    private final Map<String, Region> regions = new ConcurrentHashMap<>();

    public JenaFactStore(Dataset dataset) {
        this.dataset = dataset;
    }

    public static JenaFactStore inMemory() {
        return new JenaFactStore(DatasetFactory.createTxnMem());
    }

    @Override
    public Region region(String concept) {
        return regions.computeIfAbsent(concept, c -> new JenaRegion(dataset.getNamedModel("concept:" + c)));
    }

    private static final class JenaRegion implements Region {
        private final Model graph;

        private JenaRegion(Model graph) {
            this.graph = graph;
        }

        private static Resource subject(String id) {
            return ResourceFactory.createResource(NS + id);
        }

        private static Property predicate(String name) {
            return ResourceFactory.createProperty(NS + name);
        }

        @Override
        public Set<String> read(String subject, String predicate) {
            Set<String> values = new LinkedHashSet<>();
            graph.listObjectsOfProperty(subject(subject), predicate(predicate))
                    .forEachRemaining(node -> values.add(asString(node)));
            return values;
        }

        @Override
        public void write(String subject, String predicate, String value) {
            graph.add(subject(subject), predicate(predicate), ResourceFactory.createStringLiteral(value));
        }

        @Override
        public void remove(String subject, String predicate, String value) {
            graph.remove(subject(subject), predicate(predicate), ResourceFactory.createStringLiteral(value));
        }

        @Override
        public void clear(String subject, String predicate) {
            graph.removeAll(subject(subject), predicate(predicate), null);
        }

        @Override
        public Set<String> subjects(String predicate, String value) {
            Set<String> result = new LinkedHashSet<>();
            graph.listSubjectsWithProperty(predicate(predicate), ResourceFactory.createStringLiteral(value))
                    .forEachRemaining(resource -> result.add(resource.getURI().substring(NS.length())));
            return result;
        }

        @Override
        public List<Fact> facts() {
            List<Fact> result = new ArrayList<>();
            for (Statement s : graph.listStatements().toList()) {
                result.add(new Fact(
                        s.getSubject().getURI().substring(NS.length()),
                        s.getPredicate().getURI().substring(NS.length()),
                        asString(s.getObject())));
            }
            return result;
        }

        private static String asString(RDFNode node) {
            return node.isLiteral() ? node.asLiteral().getString() : node.toString();
        }
    }
}
