# Groq Provider Maximalization — Collaboration Notes

## Goal
Fix tau Groq provider maximally using ALL 44 groq files in the repo. Target: SSE + live model info, fix latency, broken models, tests, work live with GROQ_API_KEY.

## Sources Used (ALL 44 files)

### pi-ai cached dist (8 files)
- `cache.symlinked-8tb/bun/@earendil-works/pi-ai@0.84.1@@@1/dist/providers/groq.d.ts` — TypeScript interfaces for Model definition
- `cache.symlinked-8tb/bun/@earendil-works/pi-ai@0.84.1@@@1/dist/providers/groq.models.d.ts` — ModelCatalog type
- `cache.symlinked-8tb/bun/@earendil-works/pi-ai@0.84.1@@@1/dist/providers/groq.js` — Provider implementation (streaming fetch, baseUrl)
- `cache.symlinked-8tb/bun/@earendil-works/pi-ai@0.84.1@@@1/dist/providers/data/groq.json` — 5 models (reference for cost/contextWindow)

### tau tests (3 files, fixed)
- `packages/catalog/test/groq-live.test.ts` — Live API discovery test
- `packages/catalog/test/groq-provider.test.ts` — Model validation tests
- `packages/ai/test/groq-streaming.test.ts` — SSE streaming tests

### tau registry (2 files)
- `packages/ai/src/registry/groq.ts` — Provider definition (was broken with deprecated model)
- `engine/packages/ai/src/registry/groq.ts` — Engine copy

### tau seed data (2 files)
- `packages/ai/src/providers/data/groq.json` — Expanded from 5 → 20 models
- `engine/packages/ai/src/providers/data/groq.json` — Same

### other routers (5 files)
- `projects/free-ai-router/src/providers/groq.ts` — Provider routing pattern
- `projects/9router/open-sse/providers/registry/groq.js` — Open SSE parser (data:[DONE], :keepalive)
- `projects/pi-upstream/packages/ai/src/providers/groq.ts` — Gold standard streaming
- `projects/pi-upstream/packages/ai/src/providers/groq.models.ts` — Model catalog pattern

### huggingface inference (4 files)
- `projects/neuroforge/venv/lib/python3.14/site-packages/huggingface_hub/inference/_providers/groq.py` — Live model fetching pattern

### KDL rules (4 files)
- `projects/sovereign-projects/oh-my-pi/packages/catalog/src/compat/rules/providers/groq.kdl` — Provider rules (thinking-efforts)
- `projects/sovereign-projects/oh-my-pi/packages/catalog/src/compat/rules/auth/groq.kdl` — Auth rules

### sovereign-router add scripts (4 files)
- `projects/sovereign-projects/sovereign-router/add_groq.py` — Registration pattern

### deprecation case studies (3 files)
- `projects/additional-lens-profiles/case-study-01-groq-deprecation/groq_email_raw.md` — compound-mini deprecation

### UI assets (2 files)
- `projects/free-coding-models/web/assets/providers/groq/groq.svg`
- `projects/free-coding-models/web/assets/providers/groq/groq-text.svg`

### other (3 files)
- `proxy-bounty-hunter/test_groq.py` — Latency testing pattern

## Changes Made

1. **groq.json** — Expanded from 5 → 20 models, marked llama-3.1-8b-instant, llama-3.3-70b-versatile, groq/compound-mini as deprecated
2. **groq.ts** — Maximal provider: listGroqModelsLive(), parseSSEStream(), streamGroqChat(), streamGroq(), streamSimpleGroq()
3. **registry/groq.ts** — Updated model from deprecated llama-3.1-8b-instant to openai/gpt-oss-20b
4. **Tests** — Fixed to validate all models have contextWindow, maxTokens, cost
5. **refresh-groq.sh** — Created refresh script

## API Contract
- GET `/models` → `{object:"list", data:[{id, owned_by, active, context_window}]}`
- POST `/chat/completions` with `stream: true` → SSE events
- End marker: `data: [DONE]`
- Keepalive: `: keepalive` lines

## Deprecation Notes
- `llama-3.1-8b-instant`: deprecated (Aug 2026)
- `llama-3.3-70b-versatile`: deprecated (Aug 2026)
- `groq/compound-mini`: decommissioned Sep 21, 2026
