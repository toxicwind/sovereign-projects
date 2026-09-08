# Endless TODO — packages/ Loop (mirrors root, never finite)

> Infinite loop for packages/* — append-only.

## Wave Groq Maximal 2026-09-03
- [x] groq registry login via createApiKeyLogin (gsk_...) — `packages/ai/src/registry/groq.ts`
- [x] catalogDiscovery Groq + default llama-3.3-70b-versatile — `packages/catalog/src/provider-models/descriptors.ts` + `openai-compat.ts` + `hosts.ts` + `compat/openai.ts`
- [x] groq streaming/tool/JSON parity tests (4 pass) — `packages/ai/test/groq-streaming.test.ts` + `packages/catalog/test/groq-provider.test.ts`
- [ ] next: live generate with GROQ_API_KEY nightly, whisper audio filter audit, mixtral deprecation watch

## Next Wave (open)
- [ ] packages/catalog live nightly
- [ ] packages/ai whisper audit
- [ ] packages/engine parity flush

---
*Loop rule: append-only, never finite.*
