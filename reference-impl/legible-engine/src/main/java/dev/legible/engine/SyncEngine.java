package dev.legible.engine;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * The engine: dispatches actions to concepts, appends invocations and
 * completions to a per-flow log, and — only after a completion is committed —
 * evaluates matching syncs (fire-after-commit).
 *
 * <p><strong>Concurrency model.</strong> Each {@link #run} call owns a private
 * {@link ActionLog} (sharded by flow token), so flows never share mutable log
 * state and the log is never a contention point. The two remaining shared
 * resources are handled as follows:
 * <ul>
 *   <li><strong>Concept state</strong> ({@link FactStore}) — a concept is a
 *       state machine, so its actions are serialized per concept
 *       ({@link #execute}); each action is the atomic unit.</li>
 *   <li><strong>Archive buffer/sink</strong> — already thread-safe.</li>
 * </ul>
 *
 * <p>There is no transaction and no rollback. A downstream action that fails
 * simply completes with a named {@code error} outcome. Replay of a crashed flow
 * is {@link #drain(ActionLog)} over that flow's log.
 */
public final class SyncEngine {

    private final FactStore facts;
    private final Map<String, Concept> concepts;
    private final List<SyncRule> rules;
    /**
     * Trigger index: {@code concept/action/outcome} -> the ordered rules that
     * match that trigger. A rule with {@code triggerOutcome == null} is filed
     * under bare {@code concept/action} and returned for every outcome. Replaces
     * the linear {@code for (rule : rules)} scan in the drain loop — same order
     * and exactly-once semantics, but O(matching rules) not O(all rules) per
     * completion.
     */
    private final Map<String, List<IndexEntry>> triggerIndex;

    /** One index entry: the rule and which of its conjuncts is filed here. */
    private record IndexEntry(SyncRule rule, int conjunct) {}
    private final FlowArchiver archiver;
    private final Map<String, ActionLog> inFlight = new ConcurrentHashMap<>();
    private final Map<String, Object> conceptLocks = new ConcurrentHashMap<>();

    public SyncEngine(FactStore facts, List<Concept> concepts, List<SyncRule> rules) {
        this(facts, concepts, rules,
                new FlowArchiver(FlowArchiveSink.DEVNULL, new FlowArchiveBuffer(100)));
    }

    public SyncEngine(FactStore facts, List<Concept> concepts, List<SyncRule> rules,
                      FlowArchiver archiver) {
        this.facts = facts;
        this.concepts = new LinkedHashMap<>();
        for (Concept c : concepts) {
            this.concepts.put(c.name(), c);
        }
        this.rules = List.copyOf(rules);
        this.triggerIndex = buildTriggerIndex(this.rules);
        this.archiver = archiver;
    }

    /**
     * Build the {@code concept/action/outcome} -> entries index (order-preserving).
     * Every conjunct of a (possibly synchronised) rule is filed, so a completion
     * for any conjunct surfaces the rule for the completeness check.
     */
    private static Map<String, List<IndexEntry>> buildTriggerIndex(List<SyncRule> rules) {
        Map<String, List<IndexEntry>> index = new HashMap<>();
        for (SyncRule rule : rules) {
            for (int i = 0; i < rule.triggers.size(); i++) {
                SyncRule.Trigger t = rule.triggers.get(i);
                IndexEntry entry = new IndexEntry(rule, i);
                index.computeIfAbsent(t.concept() + "/" + t.action(),
                        k -> new ArrayList<>()).add(entry);
                if (t.outcome() != null) {
                    index.computeIfAbsent(key(t.concept(), t.action(), t.outcome()),
                            k -> new ArrayList<>()).add(entry);
                }
            }
        }
        return index;
    }

    private static String key(String concept, String action, String outcome) {
        return concept + "/" + action + "/" + outcome;
    }

    /**
     * Candidate rules whose conjunct matches {@code (concept, action, outcome,
     * input)} — the exact outcome bucket plus any-outcome entries for that
     * {@code concept/action}, in declaration order, filtered by the matched
     * conjunct's input-pattern matcher (R15; ABSENT sentinel honoured).
     */
    private List<IndexEntry> candidateEntries(String concept, String action, String outcome,
                                              Map<String, Object> input) {
        List<IndexEntry> exact = triggerIndex.get(key(concept, action, outcome));
        List<IndexEntry> any = triggerIndex.get(concept + "/" + action);
        if (exact == null && any == null) {
            return List.of();
        }
        Set<IndexEntry> ordered = new LinkedHashSet<>();
        if (exact != null) ordered.addAll(exact);
        if (any != null) ordered.addAll(any);
        List<IndexEntry> result = new ArrayList<>(ordered.size());
        for (IndexEntry entry : ordered) {
            SyncRule.Trigger t = entry.rule().triggers.get(entry.conjunct());
            if (patternMatches(t.inputPattern(), input)) {
                result.add(entry);
            }
        }
        return result;
    }

    /**
     * Match every conjunct of {@code rule} against the flow's committed
     * completions, returning the matched context, or {@code null} when some
     * conjunct has no match yet. The latest matching invocation wins per
     * conjunct (deterministic by flow order).
     */
    private Conjuncts matchConjuncts(SyncRule rule, ActionLog flowLog, String flowId) {
        Map<String, Invocation> invs = new LinkedHashMap<>();
        Map<String, Completion> comps = new LinkedHashMap<>();
        for (SyncRule.Trigger t : rule.triggers) {
            Invocation found = null;
            for (Invocation i : flowLog.invocations(flowId)) {
                if (!i.concept().equals(t.concept()) || !i.action().equals(t.action())) continue;
                Optional<Completion> c = flowLog.completion(i.actionId());
                if (c.isEmpty()) continue;
                if (t.outcome() != null && !t.outcome().equals(c.get().outcome())) continue;
                if (!patternMatches(t.inputPattern(), i.input())) continue;
                found = i;
            }
            if (found == null) return null;
            invs.put(t.name(), found);
            comps.put(t.name(), flowLog.completion(found.actionId()).orElseThrow());
        }
        return new Conjuncts(invs, comps);
    }

    static boolean patternMatches(Map<String, Object> pattern,
                                          Map<String, Object> input) {
        if (pattern == null) return true;
        for (Map.Entry<String, Object> e : pattern.entrySet()) {
            if (e.getValue() == Dsl.ABSENT) {
                // Absent == no value: the key is missing OR carries null.
                // This engine's arg builder always inserts a key (null for an
                // unbound/empty source), so both shapes must match.
                if (input.get(e.getKey()) != null) return false;
                continue;
            }
            if (!input.containsKey(e.getKey())) return false;
            if (!e.getValue().equals(input.get(e.getKey()))) return false;
        }
        return true;
    }

    public FactStore facts() {
        return facts;
    }

    public List<SyncRule> rules() {
        return rules;
    }

    public FlowArchiver archiver() {
        return archiver;
    }

    /** In-flight flow logs by flow token (introspection). */
    public Map<String, ActionLog> inFlight() {
        return inFlight;
    }

    /** Introspection surface (the Jena profile's {@code /api/dev/*} endpoints). */
    public DebugApi debug() {
        return new DebugApi(inFlight, facts, rules, archiver.buffer());
    }

    /**
     * Run a flow from a root action, driving it to quiescence on its own
     * private log. Thread-safe: concurrent callers each get their own flow log.
     *
     * @return the {@code Web/respond} completion fields, or {@code null} if the
     *         flow terminated without a response.
     */
    public Map<String, Object> run(String concept, String action, Map<String, Object> input) {
        String flowId = UUID.randomUUID().toString();
        ActionLog flowLog = new InMemoryActionLog();
        inFlight.put(flowId, flowLog);
        try {
            mint(flowLog, concept, action, input, flowId, null, null);
            drain(flowLog);
            return flowLog.completionByFlowAction(flowId, "Web", "respond")
                    .map(Completion::fields)
                    .orElse(null);
        } finally {
            inFlight.remove(flowId);
            archiver.archive(flowId, flowLog);
        }
    }

    /**
     * Replay entry point: re-process a flow's log to quiescence. Idempotent —
     * an invocation whose completion is already recorded is skipped.
     */
    public void drain(ActionLog flowLog) {
        WhereEvaluator evaluator = new WhereEvaluator(facts, flowLog);
        Deque<String> pending = new ArrayDeque<>();
        for (Invocation inv : flowLog.invocations()) {
            if (flowLog.completion(inv.actionId()).isEmpty()) {
                pending.add(inv.actionId());
            }
        }
        while (!pending.isEmpty()) {
            String id = pending.poll();
            if (flowLog.completion(id).isPresent()) continue;
            Invocation inv = flowLog.invocation(id).orElse(null);
            if (inv == null) continue;
            processInvocation(flowLog, evaluator, inv, pending);
        }
    }

    private void mint(ActionLog flowLog, String concept, String action, Map<String, Object> input,
                      String flowId, String parent, String causedBySync) {
        String id = "a-" + UUID.randomUUID();
        flowLog.appendInvocation(new Invocation(id, flowId, parent, causedBySync,
                concept, action, input, System.currentTimeMillis()));
    }

    private void processInvocation(ActionLog flowLog, WhereEvaluator evaluator,
                                   Invocation inv, Deque<String> pending) {
        Concept c = concepts.get(inv.concept());
        Map<String, Object> output;
        try {
            output = (c == null)
                    ? Map.of("outcome", "error", "message", "unknown concept: " + inv.concept())
                    : execute(inv.concept(), c, inv.action(), inv.input());
        } catch (Exception ex) {
            output = Map.of("outcome", "error", "message",
                    ex.getClass().getSimpleName() + ": " + ex.getMessage());
        }
        String outcome = output.get("outcome") == null ? "error" : String.valueOf(output.get("outcome"));
        Map<String, Object> fields = new LinkedHashMap<>();
        output.forEach((k, v) -> {
            if (!"outcome".equals(k)) fields.put(k, v);
        });

        // Fire-after-commit: the completion is committed before any sync runs.
        flowLog.appendCompletion(new Completion(inv.actionId(), inv.flowId(), inv.concept(),
                inv.action(), outcome, fields, System.currentTimeMillis()));

        // Look up only the entries whose conjunct matches this completion, via
        // the index built at construction — not a scan of every rule.
        for (IndexEntry entry : candidateEntries(inv.concept(), inv.action(), outcome, inv.input())) {
            SyncRule rule = entry.rule();
            Conjuncts conjuncts = matchConjuncts(rule, flowLog, inv.flowId());
            if (conjuncts == null) continue; // not all conjuncts present yet
            SyncRule.Trigger primary = rule.triggers.get(0);
            Invocation primaryInv = conjuncts.invocation(primary.name());
            Completion primaryComp = conjuncts.completion(primary.name());
            if (flowLog.hasEmission(primaryInv.actionId(), rule.name)) continue; // exactly-once
            for (Map<String, Object> frame : evaluator.evaluate(rule, primaryInv, primaryComp, conjuncts)) {
                for (ThenInvocation then : rule.then) {
                    Map<String, Object> args = new LinkedHashMap<>();
                    then.args().forEach((k, src) ->
                            args.put(k, resolveScalar(evaluator, src, frame, primaryInv, primaryComp, conjuncts)));
                    String newId = "a-" + UUID.randomUUID();
                    flowLog.appendInvocation(new Invocation(newId, inv.flowId(), primaryInv.actionId(),
                            rule.name, then.concept(), then.action(), args, System.currentTimeMillis()));
                    pending.add(newId);
                }
            }
        }
    }

    /**
     * Execute a concept action atomically with respect to that concept: a
     * concept is a state machine, so only one of its actions runs at a time.
     * This is what makes "the action is the atomic unit" hold under concurrency,
     * without touching the storage layer.
     */
    private Map<String, Object> execute(String conceptName, Concept c, String action,
                                        Map<String, Object> input) {
        synchronized (conceptLocks.computeIfAbsent(conceptName, k -> new Object())) {
            return c.execute(action, input);
        }
    }

    private Object resolveScalar(WhereEvaluator evaluator, Source src, Map<String, Object> frame,
                                 Invocation inv, Completion comp, Conjuncts conjuncts) {
        List<Object> values = evaluator.resolve(src, frame, inv, comp, conjuncts);
        return values.isEmpty() ? null : values.get(0);
    }
}
