package dev.legible.engine;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;

class DebugArchiveTest {

    @Test
    void archivedListsCompletedFlowsNewestFirst() {
        FlowArchiveBuffer buffer = new FlowArchiveBuffer(4);
        buffer.add(new FlowRecord("f-1", List.of(), List.of()));
        buffer.add(new FlowRecord("f-2", List.of(), List.of()));
        DebugApi api = new DebugApi(Map.of(), new InMemoryFactStore(), List.of(), buffer);

        List<Map<String, Object>> archived = api.archived();
        assertEquals(List.of("f-2", "f-1"),
                archived.stream().map(row -> row.get("flowId")).toList());
        assertEquals(0, archived.get(0).get("actionCount"));
        assertEquals(4, api.archiveInfo().get("capacity"));
        assertEquals(0L, api.archiveInfo().get("evicted"));

        buffer.add(new FlowRecord("f-3", List.of(), List.of()));
        buffer.add(new FlowRecord("f-4", List.of(), List.of()));
        buffer.add(new FlowRecord("f-5", List.of(), List.of()));
        assertEquals(1L, api.archiveInfo().get("evicted"));
    }
}
