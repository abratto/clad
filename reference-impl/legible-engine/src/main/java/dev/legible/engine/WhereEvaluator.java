package dev.legible.engine;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Evaluates a sync's declarative {@code where} clauses into a set of frames
 * (variable bindings), one per distinct match. This is the paper's "frames"
 * model: fan-out is the result of the clause set, not of loops (R3).
 */
public final class WhereEvaluator {

    private final FactStore facts;
    private final ActionLog log;

    public WhereEvaluator(FactStore facts, ActionLog log) {
        this.facts = facts;
        this.log = log;
    }

    /**
     * Evaluate a rule's {@code where} block for a completed trigger action.
     * Returns one frame per surviving binding set.
     */
    public List<Map<String, Object>> evaluate(SyncRule rule, Invocation inv, Completion comp) {
        return evaluate(rule, inv, comp, Conjuncts.EMPTY);
    }

    /** Evaluate with matched join conjuncts available to conjunct sources. */
    public List<Map<String, Object>> evaluate(SyncRule rule, Invocation inv, Completion comp,
                                              Conjuncts conjuncts) {
        List<Map<String, Object>> frames = new ArrayList<>();
        frames.add(new LinkedHashMap<>());
        for (Clause clause : rule.where) {
            if (frames.isEmpty() && clause instanceof Clause.CollectBy) {
                // Empty-safe frame-set aggregate: an aggregate over ZERO frames
                // still emits one frame carrying the empty list — a zero-item
                // collection is a value, not an absence. Without this a
                // fan-out over an empty relation yields no frames, so the
                // aggregate (and any downstream join) never runs (conduit
                // rebuild experiment UC-07: an article with no comments must
                // still answer 200 {"comments": []}).
                frames.add(new LinkedHashMap<>());
            }
            if (clause instanceof Clause.CollectBy cb) {
                frames = collectBy(frames, cb, inv, comp, conjuncts);
            } else {
                List<Map<String, Object>> next = new ArrayList<>();
                for (Map<String, Object> frame : frames) {
                    next.addAll(apply(clause, frame, inv, comp, conjuncts));
                }
                frames = next;
            }
            // Note: no early return on an empty frame set — a later CollectBy
            // clause must still run (empty-safe aggregate above); other
            // clauses over an empty set yield empty naturally.
        }
        if (rule.groupBy != null) {
            frames = dedupByGroup(frames, rule.groupBy);
        }
        return frames;
    }

    public List<Object> resolve(Source s, Map<String, Object> frame, Invocation inv, Completion comp) {
        return resolve(s, frame, inv, comp, Conjuncts.EMPTY);
    }

    /** Resolve a source to zero or more values against a frame and trigger context. */
    public List<Object> resolve(Source s, Map<String, Object> frame, Invocation inv, Completion comp,
                                Conjuncts conjuncts) {
        if (s instanceof Source.Literal l) return List.of(l.value());
        if (s instanceof Source.VarRef r) {
            Object v = frame.get(r.var());
            return v == null ? List.of() : List.of(v);
        }
        if (s instanceof Source.Uuid) return List.of(UUID.randomUUID().toString());
        if (s instanceof Source.TriggerInput t) {
            Object v = inv.input().get(t.field());
            return v == null ? List.of() : List.of(v);
        }
        if (s instanceof Source.TriggerField t) {
            Object v = comp.fields().get(t.field());
            return v == null ? List.of() : List.of(v);
        }
        if (s instanceof Source.ConjunctInput ci) {
            Invocation i = conjuncts.invocation(ci.conjunct());
            Object v = i == null ? null : i.input().get(ci.field());
            return v == null ? List.of() : List.of(v);
        }
        if (s instanceof Source.ConjunctField cf) {
            Completion c = conjuncts.completion(cf.conjunct());
            Object v = c == null ? null : c.fields().get(cf.field());
            return v == null ? List.of() : List.of(v);
        }
        if (s instanceof Source.SiblingInput si) {
            List<Object> out = new ArrayList<>();
            for (Invocation i : log.invocations(inv.flowId())) {
                if (i.concept().equals(si.concept()) && i.action().equals(si.action())) {
                    Object v = i.input().get(si.field());
                    if (v != null) out.add(v);
                }
            }
            return out;
        }
        if (s instanceof Source.SiblingField sf) {
            return log.completionByFlowAction(inv.flowId(), sf.concept(), sf.action())
                    .map(c -> c.fields().get(sf.field()))
                    .filter(v -> v != null)
                    .map(List::of)
                    .orElseGet(List::of);
        }
        if (s instanceof Source.StateRead sr) {
            List<Object> out = new ArrayList<>();
            for (Object subj : resolve(sr.subject(), frame, inv, comp, conjuncts)) {
                out.addAll(facts.region(sr.concept()).read(String.valueOf(subj), sr.predicate()));
            }
            return out;
        }
        if (s instanceof Source.Subjects sj) {
            List<Object> objs = resolve(sj.object(), frame, inv, comp, conjuncts);
            if (objs.isEmpty()) {
                return List.of(); // object absent -> no collected value
            }
            java.util.TreeSet<String> collected = new java.util.TreeSet<>();
            for (Object obj : objs) {
                collected.addAll(
                        facts.region(sj.concept()).subjects(sj.predicate(), String.valueOf(obj)));
            }
            // ONE value: the collected subject list (deterministic order).
            return List.of(new ArrayList<>(collected));
        }
        if (s instanceof Source.Collect c) {
            return List.of(sortedValues(resolve(c.inner(), frame, inv, comp, conjuncts)));
        }
        if (s instanceof Source.Distinct d) {
            return List.of(distinctSorted(resolve(d.inner(), frame, inv, comp, conjuncts)));
        }
        if (s instanceof Source.Scan sc) {
            List<Object> vals = new ArrayList<>();
            for (Fact f : facts.region(sc.concept()).facts()) {
                if (f.predicate().equals(sc.predicate())) vals.add(f.value());
            }
            return List.of(distinctSorted(vals));
        }
        throw new IllegalStateException("unknown source: " + s);
    }

    /** Deterministically ordered (by string value) copy of {@code values}; duplicates kept. */
    private static List<Object> sortedValues(List<Object> values) {
        List<Object> out = new ArrayList<>(values);
        out.sort(java.util.Comparator.comparing(String::valueOf));
        return out;
    }

    /** De-duplicated, deterministically ordered copy of {@code values}. */
    private static List<Object> distinctSorted(List<Object> values) {
        java.util.TreeMap<String, Object> byKey = new java.util.TreeMap<>();
        for (Object v : values) {
            if (v != null) byKey.putIfAbsent(String.valueOf(v), v);
        }
        return new ArrayList<>(byKey.values());
    }

    /** Group the current frames by {@code groupKey} (null = one group), gathering a source per group. */
    private List<Map<String, Object>> collectBy(List<Map<String, Object>> frames,
                                                Clause.CollectBy cb,
                                                Invocation inv, Completion comp,
                                                Conjuncts conjuncts) {
        Map<String, Map<String, Object>> base = new LinkedHashMap<>();
        Map<String, List<Object>> gathered = new LinkedHashMap<>();
        for (Map<String, Object> frame : frames) {
            String key = cb.groupKey() == null ? "" : String.valueOf(frame.get(cb.groupKey()));
            base.computeIfAbsent(key, k -> new LinkedHashMap<>(frame));
            for (Object v : resolve(cb.source(), frame, inv, comp, conjuncts)) {
                gathered.computeIfAbsent(key, k -> new ArrayList<>()).add(v);
            }
        }
        List<Map<String, Object>> out = new ArrayList<>();
        for (Map.Entry<String, Map<String, Object>> e : base.entrySet()) {
            Map<String, Object> nf = new LinkedHashMap<>(e.getValue());
            nf.put(cb.var(), sortedValues(gathered.getOrDefault(e.getKey(), List.of())));
            out.add(nf);
        }
        return out;
    }

    private List<Map<String, Object>> apply(Clause clause, Map<String, Object> frame,
                                            Invocation inv, Completion comp, Conjuncts conjuncts) {
        if (clause instanceof Clause.Bind b) {
            return bind(b.var(), b.source(), frame, inv, comp, conjuncts);
        }
        if (clause instanceof Clause.FanOut f) {
            List<Map<String, Object>> out = new ArrayList<>();
            for (Object obj : resolve(f.object(), frame, inv, comp, conjuncts)) {
                Set<String> subjects = facts.region(f.concept()).subjects(f.predicate(), String.valueOf(obj));
                for (String s : subjects) {
                    Map<String, Object> nf = new LinkedHashMap<>(frame);
                    nf.put(f.var(), s);
                    out.add(nf);
                }
            }
            return out;
        }
        if (clause instanceof Clause.Guard g) {
            Object bound = frame.get(g.var());
            List<Object> expected = resolve(g.expected(), frame, inv, comp, conjuncts);
            if (bound == null || expected.isEmpty()) return List.of();
            for (Object e : expected) {
                if (String.valueOf(e).equals(String.valueOf(bound))) return List.of(frame);
            }
            return List.of();
        }
        if (clause instanceof Clause.OptionalClause o) {
            List<Map<String, Object>> inner = apply(o.inner(), frame, inv, comp, conjuncts);
            return inner.isEmpty() ? List.of(frame) : inner;
        }
        throw new IllegalStateException("unknown clause: " + clause);
    }

    private List<Map<String, Object>> bind(String var, Source source, Map<String, Object> frame,
                                           Invocation inv, Completion comp, Conjuncts conjuncts) {
        List<Map<String, Object>> out = new ArrayList<>();
        for (Object v : resolve(source, frame, inv, comp, conjuncts)) {
            Map<String, Object> nf = new LinkedHashMap<>(frame);
            nf.put(var, v);
            out.add(nf);
        }
        return out;
    }

    private static List<Map<String, Object>> dedupByGroup(List<Map<String, Object>> frames, String key) {
        Map<Object, Map<String, Object>> seen = new LinkedHashMap<>();
        for (Map<String, Object> frame : frames) {
            seen.putIfAbsent(frame.get(key), frame);
        }
        return new ArrayList<>(seen.values());
    }
}
