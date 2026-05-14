# LOCAL_LLM.md - context management overlay for local model runs

Use this overlay when running CLAD with local models (for example via Roo)
where long sessions can degrade quality or trigger context-window limits.

This overlay is optional. It does not replace `AGENTS.md`, stage contracts,
or gate rules.

## Goal

Keep long-running feature work stable by combining:

1. Roo context condensing
2. `RESUME.md` as continuous working memory
3. Tight file-reading discipline

## Recommended Roo settings

In Roo settings, under context management:

1. Keep intelligent context condensing enabled.
2. Set condense threshold to around 80% (instead of waiting for 100%).
3. Add a custom condense prompt that preserves CLAD-critical state.

Suggested condense prompt:

```text
Preserve these items exactly while condensing:
- Current feature and stage, including gate status.
- Latest RESUME.md contents and field values.
- Current failing command, error message, and stack trace snippets.
- File paths touched and exact next steps.
- Last attempted fixes and their outcomes.

Do not drop symbol names, method signatures, enum values, imports,
or package names.
```

## Working-memory contract

Treat `features/UC-XX-<slug>/RESUME.md` as the canonical per-feature
working memory during an active stage.

Definition of turn:

- A turn is one user message plus one agent response cycle.

At the end of every turn, update `RESUME.md` with:

1. Current stage and gate status (for example: `04d - in progress`)
2. Current blocker (or `none`)
3. Current failing command and a short error snippet (<= 20 lines)
4. Files touched this turn
5. Next 1-3 concrete steps and the next file to open

At stage approval, also refresh the gate snapshot fields required by
`AGENTS.md` rule 9 before committing.

## Read-discipline rules for long sessions

1. Do not paste whole files into chat unless explicitly asked.
2. Quote only the minimum lines needed to justify a decision.
3. Avoid re-reading large stable docs in the same stage unless a gate
   decision depends on them.
4. Prefer section headings and file paths over long restatements.

## Recovery workflow

If context quality drops or condensing occurs:

1. Update `RESUME.md` first.
2. Start a fresh session.
3. Resume using `HANDOVER.md` plus `RESUME.md`.

This keeps stage continuity even when conversation history is summarized.