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
        // INSERT into archive graph, then DELETE from action graph.
        // Matches LocalStorage.doArchive so all backends have identical
        // archive semantics — completed flows survive in the archive.
        updateBatch(List.of(
            moveStandard(flowToken, true),
            moveStar(flowToken, true)));
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

    @Override public boolean isBatching() { return batched.get() != null; }

    private static String moveStandard(String ft, boolean archive) {
        String s = RdfVocabulary.ACTION_SCHEMA_IRI;
        String a = RdfVocabulary.ACTION_GRAPH_IRI;
        String arc = RdfVocabulary.ACTION_ARCHIVE_GRAPH_IRI;
        String del = "DELETE { GRAPH <" + a + "> { ?s ?p ?o } }\n";
        String ins = archive ? "INSERT { GRAPH <" + arc + "> { ?s ?p ?o } }\n" : "";
        return "PREFIX : <" + s + ">\n" + del + ins
            + "WHERE { GRAPH <" + a + "> { ?a :flow <" + ft + "> ."
            + " { ?a ?p ?o . BIND(?a AS ?s) }"
            + " UNION { ?a :input ?s . ?s ?p ?o } } }\n";
    }

    private static String moveStar(String ft, boolean archive) {
        String s = RdfVocabulary.ACTION_SCHEMA_IRI;
        String a = RdfVocabulary.ACTION_GRAPH_IRI;
        String arc = RdfVocabulary.ACTION_ARCHIVE_GRAPH_IRI;
        String del = "DELETE { GRAPH <" + a + "> { << ?a :outcome ?outcome >> ?p ?o } }\n";
        String ins = archive ? "INSERT { GRAPH <" + arc + "> { << ?a :outcome ?outcome >> ?p ?o } }\n" : "";
        return "PREFIX : <" + s + ">\n" + del + ins
            + "WHERE { GRAPH <" + a + "> { ?a :flow <" + ft + "> ."
            + " << ?a :outcome ?outcome >> ?p ?o . } }\n";
    }

    RDFLink link() { return link; }
}
