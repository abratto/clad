package com.example.app.engine;

import org.apache.jena.query.*;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.rdflink.RDFLink;
import org.apache.jena.rdflink.RDFLinkHTTP;
import org.apache.jena.update.UpdateFactory;

import java.util.*;

public class RemoteStorage implements Storage {

    private final RDFLink link;
    private final Dataset localDataset;
    private final ThreadLocal<List<String>> batched = new ThreadLocal<>();

    public RemoteStorage(String endpoint) {
        this.link = RDFLinkHTTP.service(endpoint).build();
        this.localDataset = DatasetFactory.createTxnMem();
    }

    @Override
    public Dataset dataset() { return localDataset; }

    @Override
    public void update(String sparqlUpdate) {
        List<String> b = batched.get();
        if (b != null) { b.add(sparqlUpdate); return; }
        link.update(UpdateFactory.create(sparqlUpdate));
    }

    @Override
    public void updateBatch(List<String> sparqlUpdates) {
        if (sparqlUpdates.isEmpty()) return;
        List<String> b = batched.get();
        if (b != null) { b.addAll(sparqlUpdates); return; }
        StringBuilder sb = new StringBuilder();
        for (String u : sparqlUpdates) sb.append(u).append(" ;\n");
        link.update(UpdateFactory.create(sb.toString()));
    }

    @Override
    public Model construct(String sparqlConstruct) {
        return ModelFactory.createModelForGraph(link.queryConstruct(sparqlConstruct));
    }

    @Override
    public boolean ask(String sparqlAsk) {
        return link.queryAsk(sparqlAsk);
    }

    @Override
    public List<Map<String, String>> select(String sparqlSelect) {
        List<Map<String, String>> rows = new ArrayList<>();
        link.querySelect(sparqlSelect, binding -> {
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
        deleteFlow(flowToken);
    }

    @Override public void beginBatch() { batched.set(new ArrayList<>()); }

    @Override
    public void flushBatch() {
        List<String> queued = batched.get();
        if (queued == null || queued.isEmpty()) { batched.remove(); return; }
        batched.remove();
        StringBuilder sb = new StringBuilder();
        for (String u : queued) sb.append(u).append(" ;\n");
        link.update(UpdateFactory.create(sb.toString()));
    }

    @Override public void abortBatch() { batched.remove(); }

    private void deleteFlow(String flowToken) {
        String s = RdfVocabulary.ACTION_SCHEMA_IRI;
        String a = RdfVocabulary.ACTION_GRAPH_IRI;
        String sparql = "PREFIX : <" + s + ">\n"
            + "DELETE { GRAPH <" + a + "> { ?s ?p ?o } }\n"
            + "WHERE { GRAPH <" + a + "> { ?a :flow <" + flowToken + "> ."
            + " { ?a ?p ?o . BIND(?a AS ?s) }"
            + " UNION { ?a :input ?s . ?s ?p ?o } } };\n"
            + "DELETE { GRAPH <" + a + "> { << ?a :outcome ?o >> ?p ?v } }\n"
            + "WHERE { GRAPH <" + a + "> { ?a :flow <" + flowToken + "> ."
            + " << ?a :outcome ?o >> ?p ?v . } }";
        link.update(UpdateFactory.create(sparql));
    }

    RDFLink link() { return link; }
}
