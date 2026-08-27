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
        List<Map<String, Object>> frames = new ArrayList<>();
        frames.add(new LinkedHashMap<>());
        for (Clause clause : rule.where) {
            List<Map<String, Object>> next = new ArrayList<>();
            for (Map<String, Object> frame : frames) {
                next.addAll(apply(clause, frame, inv, comp));
            }
            frames = next;
            if (frames.isEmpty()) return frames;
        }
        if (rule.groupBy != null) {
            frames = dedupByGroup(frames, rule.groupBy);
        }
        return frames;
    }

    /** Resolve a source to zero or more values against a frame and trigger context. */
    public List<Object> resolve(Source s, Map<String, Object> frame, Invocation inv, Completion comp) {
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
            for (Object subj : resolve(sr.subject(), frame, inv, comp)) {
                out.addAll(facts.region(sr.concept()).read(String.valueOf(subj), sr.predicate()));
            }
            return out;
        }
        throw new IllegalStateException("unknown source: " + s);
    }

    private List<Map<String, Object>> apply(Clause clause, Map<String, Object> frame,
                                            Invocation inv, Completion comp) {
        if (clause instanceof Clause.Bind b) {
            return bind(b.var(), b.source(), frame, inv, comp);
        }
        if (clause instanceof Clause.FanOut f) {
            List<Map<String, Object>> out = new ArrayList<>();
            for (Object obj : resolve(f.object(), frame, inv, comp)) {
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
            List<Object> expected = resolve(g.expected(), frame, inv, comp);
            if (bound == null || expected.isEmpty()) return List.of();
            for (Object e : expected) {
                if (String.valueOf(e).equals(String.valueOf(bound))) return List.of(frame);
            }
            return List.of();
        }
        if (clause instanceof Clause.OptionalClause o) {
            List<Map<String, Object>> inner = apply(o.inner(), frame, inv, comp);
            return inner.isEmpty() ? List.of(frame) : inner;
        }
        throw new IllegalStateException("unknown clause: " + clause);
    }

    private List<Map<String, Object>> bind(String var, Source source, Map<String, Object> frame,
                                           Invocation inv, Completion comp) {
        List<Map<String, Object>> out = new ArrayList<>();
        for (Object v : resolve(source, frame, inv, comp)) {
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
