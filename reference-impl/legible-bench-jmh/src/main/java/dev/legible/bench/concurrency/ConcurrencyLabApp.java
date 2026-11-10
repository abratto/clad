package dev.legible.bench.concurrency;

import dev.legible.engine.Concept;
import dev.legible.engine.FactStore;
import dev.legible.engine.InMemoryFactStore;
import dev.legible.engine.SyncEngine;
import dev.legible.example.login.WebConcept;

import java.util.List;
import java.util.Map;

/** Throwaway app exercising per-subject and multi-subject locking. */
public final class ConcurrencyLabApp {

    private final SyncEngine engine;
    private final CounterConcept counter;
    private final AccountConcept account;

    private ConcurrencyLabApp(SyncEngine engine, CounterConcept counter, AccountConcept account) {
        this.engine = engine;
        this.counter = counter;
        this.account = account;
    }

    public static ConcurrencyLabApp create() {
        return create(new InMemoryFactStore());
    }

    public static ConcurrencyLabApp create(FactStore facts) {
        CounterConcept counter = new CounterConcept(facts.region("Counter"));
        AccountConcept account = new AccountConcept(facts.region("Account"));
        List<Concept> concepts = List.of(new WebConcept(), counter, account);
        SyncEngine engine = new SyncEngine(facts, concepts, ConcurrencyLabSyncs.all());
        return new ConcurrencyLabApp(engine, counter, account);
    }

    public Map<String, Object> increment(String counterId) {
        return engine.run("Web", "request", Map.of(
                "route", "increment",
                "counterId", counterId));
    }

    public Map<String, Object> credit(String accountId, int amount) {
        return engine.run("Web", "request", Map.of(
                "route", "credit",
                "accountId", accountId,
                "amount", amount));
    }

    public Map<String, Object> transfer(String from, String to, int amount) {
        return engine.run("Web", "request", Map.of(
                "route", "transfer",
                "from", from,
                "to", to,
                "amount", amount));
    }

    public int counterValue(String counterId) {
        return counter.current(counterId);
    }

    public int balance(String accountId) {
        return account.balance(accountId);
    }

    public void seedBalance(String accountId, int balance) {
        account.seedBalance(accountId, balance);
    }

    public SyncEngine engine() {
        return engine;
    }
}
