# LOCAL_LLM.md - context management overlay for local model runs

Use this overlay when running CLAD with local models (for example via Cline)
where long sessions can degrade quality or trigger context-window limits.

This overlay is optional. It does not replace `AGENTS.md`, stage contracts,
or gate rules.

## Goal

Keep long-running feature work stable by combining:

1. Cline Auto Compact (or equivalent summarization)
2. `RESUME.md` as continuous working memory
3. Tight file-reading discipline

## Recommended Cline settings

In Cline:

1. Keep Auto Compact enabled when your model/provider supports it.
2. Use task lists and `RESUME.md` so the session can survive summarization cleanly.
3. If you use custom summarization prompts or plugins, preserve CLAD-critical state.

Current limitation: the Cline docs describe Auto Compact behavior, but
do not document a portable repo-committed workspace settings file for a
custom compaction threshold or summarization prompt. Treat those as
local user settings unless Cline publishes a stable project-level
settings format for them.

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
Do not normalize canonical literals or tokens: preserve exact casing,
hyphenation, numeric-vs-string form, action argument names, and outcome
names exactly as written in approved artefacts.
```

## Extra guardrail for Stage 03 with local models

Before drafting sync prose, build a short token ledger from Stage 02b and
Stage 02 containing:

- source row id
- target row id
- exact `when` signature
- exact `then` signature
- allowed literals

Use that ledger as a copy source. If the signatures or literals differ
between Stage 02b and Stage 02, stop and reopen Stage 02 instead of
asking the model to reconcile them from memory.

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