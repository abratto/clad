package dev.legible.bench.jmh;

import dev.legible.engine.Fact;
import dev.legible.engine.FactStore;
import dev.legible.engine.Region;
import dev.legible.engine.TransactionalRegion;

import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Supplier;

/** Times region operations per concept for the Step 0 probe. */
public final class TimingFactStore implements FactStore {

    private final FactStore delegate;
    private final TimingStats stats;
    private final ConcurrentHashMap<String, TimingRegion> regions = new ConcurrentHashMap<>();

    public TimingFactStore(FactStore delegate, TimingStats stats) {
        this.delegate = delegate;
        this.stats = stats;
    }

    @Override
    public Region region(String concept) {
        return regions.computeIfAbsent(concept,
                c -> new TimingRegion(c, delegate.region(c), stats));
    }

    @Override
    public Region maybeRegion(String concept) {
        Region region = delegate.maybeRegion(concept);
        if (region == null) {
            return null;
        }
        return regions.computeIfAbsent(concept,
                c -> new TimingRegion(c, region, stats));
    }

    private static final class TimingRegion implements TransactionalRegion {

        private final String concept;
        private final Region delegate;
        private final TransactionalRegion transactional;
        private final TimingStats stats;

        private TimingRegion(String concept, Region delegate, TimingStats stats) {
            this.concept = concept;
            this.delegate = delegate;
            this.transactional = delegate instanceof TransactionalRegion tx ? tx : null;
            this.stats = stats;
        }

        private <T> T time(String op, Supplier<T> body) {
            long start = System.nanoTime();
            try {
                return body.get();
            } finally {
                stats.record("region:" + concept + "/" + op, System.nanoTime() - start);
            }
        }

        private void time(String op, Runnable body) {
            long start = System.nanoTime();
            try {
                body.run();
            } finally {
                stats.record("region:" + concept + "/" + op, System.nanoTime() - start);
            }
        }

        @Override
        public Set<String> read(String subject, String predicate) {
            return time("read", () -> delegate.read(subject, predicate));
        }

        @Override
        public void write(String subject, String predicate, String value) {
            time("write", () -> delegate.write(subject, predicate, value));
        }

        @Override
        public void remove(String subject, String predicate, String value) {
            time("remove", () -> delegate.remove(subject, predicate, value));
        }

        @Override
        public void clear(String subject, String predicate) {
            time("clear", () -> delegate.clear(subject, predicate));
        }

        @Override
        public Set<String> subjects(String predicate, String value) {
            return time("subjects", () -> delegate.subjects(predicate, value));
        }

        @Override
        public List<Fact> facts() {
            return time("facts", () -> delegate.facts());
        }

        @Override
        public Set<String> read(List<String> subject, String predicate) {
            return time("readComposite", () -> delegate.read(subject, predicate));
        }

        @Override
        public void write(List<String> subject, String predicate, String value) {
            time("writeComposite", () -> delegate.write(subject, predicate, value));
        }

        @Override
        public void remove(List<String> subject, String predicate, String value) {
            time("removeComposite", () -> delegate.remove(subject, predicate, value));
        }

        @Override
        public void clear(List<String> subject, String predicate) {
            time("clearComposite", () -> delegate.clear(subject, predicate));
        }

        @Override
        public Set<String> read(String member, String subject, String predicate) {
            return time("readMember", () -> delegate.read(member, subject, predicate));
        }

        @Override
        public void write(String member, String subject, String predicate, String value) {
            time("writeMember", () -> delegate.write(member, subject, predicate, value));
        }

        @Override
        public void remove(String member, String subject, String predicate, String value) {
            time("removeMember", () -> delegate.remove(member, subject, predicate, value));
        }

        @Override
        public void clear(String member, String subject, String predicate) {
            time("clearMember", () -> delegate.clear(member, subject, predicate));
        }

        @Override
        public void beginAction() {
            time("beginAction", () -> {
                if (transactional != null) {
                    transactional.beginAction();
                }
            });
        }

        @Override
        public void flushAction() {
            time("flushAction", () -> {
                if (transactional != null) {
                    transactional.flushAction();
                }
            });
        }

        @Override
        public void abortAction() {
            time("abortAction", () -> {
                if (transactional != null) {
                    transactional.abortAction();
                }
            });
        }
    }
}
