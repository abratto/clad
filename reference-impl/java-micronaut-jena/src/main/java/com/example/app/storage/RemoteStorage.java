package com.example.app.storage;

import dev.clad.engine.*;

import org.apache.jena.query.*;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.rdflink.RDFLink;
import org.apache.jena.rdflink.RDFLinkHTTP;
import org.apache.jena.update.UpdateFactory;
import org.apache.jena.update.UpdateRequest;

import java.net.Authenticator;
import java.net.PasswordAuthentication;
import java.net.http.HttpClient;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;

public class RemoteStorage implements Storage {

    private static final Duration CONNECT_TIMEOUT = Duration.ofSeconds(5);

    private final RDFLink queryLink;
    private final RDFLink updateLink;
    private final ThreadLocal<List<String>> batched = new ThreadLocal<>();

    public RemoteStorage(String endpoint) {
        this.queryLink = RDFLinkHTTP.service(endpoint)
            .httpClient(HttpClient.newBuilder().connectTimeout(CONNECT_TIMEOUT).build())
            .build();
        this.updateLink = this.queryLink;
    }

    public RemoteStorage(String endpoint, String username, String password) {
        AtomicBoolean credentialsProvided = new AtomicBoolean();
        HttpClient client = HttpClient.newBuilder()
            .connectTimeout(CONNECT_TIMEOUT)
                .authenticator(new Authenticator() {
                    @Override
                    protected PasswordAuthentication getPasswordAuthentication() {
                        if (!credentialsProvided.compareAndSet(false, true)) return null;
                        return new PasswordAuthentication(username, password.toCharArray());
                    }
                })
                .build();
        this.queryLink = RDFLinkHTTP.service(endpoint).httpClient(client).build();
        this.updateLink = this.queryLink;
    }

    /**
     * Split query/update endpoints (for Fuseki where CONSTRUCT on /update 400s).
     * Credentialed — credentials are sent to both endpoints.
     */
    public RemoteStorage(String queryEndpoint, String updateEndpoint,
                         String username, String password) {
        AtomicBoolean credentialsProvided = new AtomicBoolean();
        HttpClient client = HttpClient.newBuilder()
            .connectTimeout(CONNECT_TIMEOUT)
                .authenticator(new Authenticator() {
                    @Override
                    protected PasswordAuthentication getPasswordAuthentication() {
                        if (!credentialsProvided.compareAndSet(false, true)) return null;
                        return new PasswordAuthentication(username, password.toCharArray());
                    }
                })
                .build();
        this.queryLink = RDFLinkHTTP.service(queryEndpoint).httpClient(client).build();
        this.updateLink = RDFLinkHTTP.service(updateEndpoint).httpClient(client).build();
    }

    /** Split endpoints without credentials. */
    RemoteStorage(String queryEndpoint, String updateEndpoint) {
        HttpClient client = HttpClient.newBuilder()
                .connectTimeout(CONNECT_TIMEOUT).build();
        this.queryLink = RDFLinkHTTP.service(queryEndpoint).httpClient(client).build();
        this.updateLink = RDFLinkHTTP.service(updateEndpoint).httpClient(client).build();
    }

    @Override
    public Dataset dataset() {
        throw new UnsupportedOperationException(
                "remote storage does not expose a local Dataset");
    }

    @Override
    public void update(String sparqlUpdate) {
        List<String> b = batched.get();
        if (b != null) { b.add(sparqlUpdate); return; }
        updateLink.update(UpdateFactory.create(sparqlUpdate));
    }

    @Override
    public void update(UpdateRequest request) {
        List<String> b = batched.get();
        if (b != null) { b.add(request.toString()); return; }
        updateLink.update(request);
    }

    @Override
    public void updateBatch(List<String> sparqlUpdates) {
        if (sparqlUpdates.isEmpty()) return;
        List<String> b = batched.get();
        if (b != null) { b.addAll(sparqlUpdates); return; }
        StringBuilder sb = new StringBuilder();
        for (String u : sparqlUpdates) sb.append(u).append(" ;\n");
        updateLink.update(UpdateFactory.create(sb.toString()));
    }

    @Override
    public Model construct(String sparqlConstruct) {
        return ModelFactory.createModelForGraph(queryLink.queryConstruct(sparqlConstruct));
    }

    @Override
    public boolean ask(String sparqlAsk) {
        return queryLink.queryAsk(sparqlAsk);
    }

    @Override
    public List<Map<String, String>> select(String sparqlSelect) {
        List<Map<String, String>> rows = new ArrayList<>();
        queryLink.querySelect(sparqlSelect, binding -> {
            Map<String, String> row = new LinkedHashMap<>();
            binding.forEach((v, n) -> {
                if (n == null) row.put(v.getVarName(), null);
                else if (n.isLiteral()) row.put(v.getVarName(), n.getLiteralLexicalForm());
                else if (n.isURI()) row.put(v.getVarName(), n.getURI());
                else row.put(v.getVarName(), n.toString());
            });
            rows.add(row);
        });
        return rows;
    }

    @Override
    public void archiveFlow(String flowToken) {
        // No-op — the action log is always in-memory in the current
        // architecture. RemoteStorage only holds durable business graphs.
        // Flow archival is handled by FlowArchiver.
    }

    @Override public void beginBatch() { batched.set(new ArrayList<>()); }

    @Override
    public void flushBatch() {
        List<String> queued = batched.get();
        if (queued == null || queued.isEmpty()) { batched.remove(); return; }
        batched.remove();
        StringBuilder sb = new StringBuilder();
        for (String u : queued) sb.append(u).append(" ;\n");
        updateLink.update(UpdateFactory.create(sb.toString()));
    }

    @Override public void abortBatch() { batched.remove(); }

    @Override public boolean isBatching() { return batched.get() != null; }

    RDFLink queryLink() { return queryLink; }
    RDFLink updateLink() { return updateLink; }
}
