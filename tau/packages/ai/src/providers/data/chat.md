# Groq Provider Maximalization — Chat Session

## Session Purpose
Fix tau Groq provider maximally using ALL 44 groq files in the repo. Target: SSE + live model info, fix latency, broken models, tests, work live with GROQ_API_KEY.

## Current Status
- Phase: Implementation complete, verification in progress
- Models in groq.json: 20 (was 5)
- Deprecated models: llama-3.1-8b-instant, llama-3.3-70b-versatile, groq/compound-mini

## Key Files Created/Modified

### Core
- `packages/ai/src/providers/groq.ts` — Maximal provider with SSE parser, live model fetch, streaming
- `packages/ai/src/providers/data/groq.json` — 20 models (expanded from 5)
- `packages/ai/src/providers/data/groq.models.ts` — Model catalog auto-generation
- `packages/ai/src/registry/groq.ts` — Registry definition (updated model to non-deprecated)

### Tests
- `packages/catalog/test/groq-live.test.ts` — Live API discovery (>=6 models, deprecated markers)
- `packages/catalog/test/groq-provider.test.ts` — Model validation (contextWindow, maxTokens, cost)
- `packages/ai/test/groq-streaming.test.ts` — SSE parsing, tool-call merging, [DONE] handling

### Supporting
- `refresh-groq.sh` — Live model refresh script
- `groq-jq-commands.md` — jq commands for analysis
- `collab.md` — Collaboration notes with all 44 source files

## API Contract
- GET `/models` → `{object:"list", data:[{id, owned_by, active, context_window}]}`
- POST `/chat/completions` with `stream: true` → SSE events
- End marker: `data: [DONE]`
- Keepalive: `: keepalive` lines

## Open Questions
1. Are the bun test imports resolving correctly? (bun uses `@oh-my-pi` aliases)
2. Does `streamOpenAICompletions` accept the full Groq request body?
3. Are the `service_tier` fields supported by tau's types?

## Verification Checklist
- [ ] bun test passes for all 3 test files
- [ ] groq.json has >=16 models with all required fields
- [ ] groq.ts compiles without errors
- [ ] SSE parser handles data:[DONE], :keepalive, empty lines
- [ ] listGroqModelsLive() works with GROQ_API_KEY
