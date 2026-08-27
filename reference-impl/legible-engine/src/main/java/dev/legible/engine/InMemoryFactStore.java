package dev.legible.engine;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/** In-memory {@link FactStore}: one relation per concept, one region per concept. */
public final class InMemoryFactStore implements FactStore {

    private final Map<String, Region> regions = new ConcurrentHashMap<>();

    @Override
    public Region region(String concept) {
        return regions.computeIfAbsent(concept, c -> new InMemoryRegion());
    }

    private static final class InMemoryRegion implements Region {
        // subject -> predicate -> values
        private final Map<String, Map<String, Set<String>>> facts = new ConcurrentHashMap<>();

        @Override
        public Set<String> read(String subject, String predicate) {
            Map<String, Set<String>> preds = facts.get(subject);
            if (preds == null) return Set.of();
            Set<String> values = preds.get(predicate);
            return values == null ? Set.of() : Set.copyOf(values);
        }

        @Override
        public void write(String subject, String predicate, String value) {
            facts.computeIfAbsent(subject, k -> new ConcurrentHashMap<>())
                    .computeIfAbsent(predicate, k -> ConcurrentHashMap.newKeySet())
                    .add(value);
        }

        @Override
        public void remove(String subject, String predicate, String value) {
            Map<String, Set<String>> preds = facts.get(subject);
            if (preds == null) return;
            Set<String> values = preds.get(predicate);
            if (values != null) values.remove(value);
        }

        @Override
        public void clear(String subject, String predicate) {
            Map<String, Set<String>> preds = facts.get(subject);
            if (preds != null) preds.remove(predicate);
        }

        @Override
        public Set<String> subjects(String predicate, String value) {
            Set<String> result = new LinkedHashSet<>();
            for (Map.Entry<String, Map<String, Set<String>>> entry : facts.entrySet()) {
                Set<String> values = entry.getValue().get(predicate);
                if (values != null && values.contains(value)) {
                    result.add(entry.getKey());
                }
            }
            return result;
        }

        @Override
        public List<Fact> facts() {
            List<Fact> out = new ArrayList<>();
            for (Map.Entry<String, Map<String, Set<String>>> e : facts.entrySet()) {
                for (Map.Entry<String, Set<String>> p : e.getValue().entrySet()) {
                    for (String v : p.getValue()) {
                        out.add(new Fact(e.getKey(), p.getKey(), v));
                    }
                }
            }
            return out;
        }
    }
}
