package dev.legible.bench.concurrency;

import dev.legible.engine.Concept;
import dev.legible.engine.Region;

import java.util.Map;
import java.util.Set;

/**
 * Lab concept: per-account balances with a multi-subject {@code transfer}.
 * {@code credit}/{@code debit} are keyed by one account; {@code transfer} declares
 * both accounts, so the engine acquires both locks in a deterministic order.
 */
public final class AccountConcept implements Concept {

    public static final String NAME = "Account";
    public static final String CREDIT = "credit";
    public static final String DEBIT = "debit";
    public static final String TRANSFER = "transfer";

    private final Region region;

    public AccountConcept(Region region) {
        this.region = region;
    }

    @Override
    public String name() {
        return NAME;
    }

    @Override
    public Object lockKey(String action, Map<String, Object> input) {
        return switch (action) {
            case CREDIT, DEBIT -> input.get("accountId");
            default -> null;
        };
    }

    @Override
    public Set<Object> lockKeys(String action, Map<String, Object> input) {
        if (TRANSFER.equals(action)) {
            return Set.of(input.get("from"), input.get("to"));
        }
        Object key = lockKey(action, input);
        return key == null ? Set.of() : Set.of(key);
    }

    @Override
    public Map<String, Object> execute(String action, Map<String, Object> input) {
        return switch (action) {
            case CREDIT -> credit(input);
            case DEBIT -> debit(input);
            case TRANSFER -> transfer(input);
            default -> Map.of("outcome", "error", "message", "unknown action: " + action);
        };
    }

    public int balance(String accountId) {
        var values = region.read(accountId, "balance");
        return values.isEmpty() ? 0 : Integer.parseInt(values.iterator().next());
    }

    public void seedBalance(String accountId, int balance) {
        region.clear(accountId, "balance");
        region.write(accountId, "balance", String.valueOf(balance));
    }

    private Map<String, Object> credit(Map<String, Object> input) {
        String accountId = (String) input.get("accountId");
        int amount = amount(input);
        if (accountId == null || amount < 0) {
            return Map.of("outcome", "error", "message", "missing accountId or negative amount");
        }
        int next = balance(accountId) + amount;
        setBalance(accountId, next);
        return Map.of("outcome", "CREDITED", "accountId", accountId, "balance", next);
    }

    private Map<String, Object> debit(Map<String, Object> input) {
        String accountId = (String) input.get("accountId");
        int amount = amount(input);
        if (accountId == null || amount < 0) {
            return Map.of("outcome", "error", "message", "missing accountId or negative amount");
        }
        int current = balance(accountId);
        if (current < amount) {
            return Map.of("outcome", "refused", "reason", "insufficient", "accountId", accountId);
        }
        int next = current - amount;
        setBalance(accountId, next);
        return Map.of("outcome", "DEBITED", "accountId", accountId, "balance", next);
    }

    private Map<String, Object> transfer(Map<String, Object> input) {
        String from = (String) input.get("from");
        String to = (String) input.get("to");
        int amount = amount(input);
        if (from == null || to == null || amount < 0) {
            return Map.of("outcome", "error", "message", "missing from/to or negative amount");
        }
        int fromBalance = balance(from);
        if (fromBalance < amount) {
            return Map.of("outcome", "refused", "reason", "insufficient", "accountId", from);
        }
        int toBalance = balance(to);
        setBalance(from, fromBalance - amount);
        setBalance(to, toBalance + amount);
        return Map.of("outcome", "TRANSFERRED", "from", from, "to", to, "amount", amount);
    }

    private void setBalance(String accountId, int balance) {
        region.clear(accountId, "balance");
        region.write(accountId, "balance", String.valueOf(balance));
    }

    private static int amount(Map<String, Object> input) {
        Object value = input.get("amount");
        if (value instanceof Number number) {
            return number.intValue();
        }
        return value == null ? 0 : Integer.parseInt(String.valueOf(value));
    }
}
