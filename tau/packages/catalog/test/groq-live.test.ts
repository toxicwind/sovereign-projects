import { describe, expect, test } from "bun:test";
import { groqModelManagerOptions } from "@oh-my-pi/pi-catalog/provider-models/openai-compat";
import { listGroqModelsLive } from "@oh-my-pi/pi-ai/providers/groq";

/**
 * Live Groq integration: hits https://api.groq.com/openai/v1/models with a real key.
 * Skips gracefully if GROQ_API_KEY is absent. Does NOT use mocks — validates live API contract.
 * Run: bun test packages/catalog/test/groq-live.test.ts
 * Or with explicit env passthrough: GROQ_API_KEY=... bun test --coverage packages/catalog/test/groq-live.test.ts
 */
const hasGroqKey = Boolean(Bun.env.GROQ_API_KEY);

describe.skipIf(!hasGroqKey)("Groq live provider discovery (requires GROQ_API_KEY)", () => {
	test("live /v1/models returns at least 6 models", async () => {
		const apiKey = Bun.env.GROQ_API_KEY!;
		const options = groqModelManagerOptions({ apiKey });
		const models = await options.fetchDynamicModels?.();
		expect(models).toBeDefined();
		expect(models!.length).toBeGreaterThanOrEqual(6);
		for (const m of models!) {
			expect(m.provider).toBe("groq");
			expect(m.api).toBe("openai-completions");
			expect(typeof m.id).toBe("string");
			expect(m.id.length).toBeGreaterThan(0);
		}
		const ids = new Set(models!.map(m => m.id));
		const anyKnown = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "openai/gpt-oss-120b", "meta-llama/llama-4-maverick-17b-128e-instruct"].some(id => ids.has(id));
		if (!anyKnown) {
			console.warn("[groq-live] warning: none of the snapshot ids found; catalog may have rotated. Got:", [...ids].slice(0, 5));
		}
		expect(models!.length).toBeGreaterThanOrEqual(6);
	});

	test("live 401 with bad key throws", async () => {
		const options = groqModelManagerOptions({ apiKey: "bad-key-live-check" });
		await expect(options.fetchDynamicModels?.()).rejects.toThrow(/HTTP 401|fetch failed/);
	});

	test("listGroqModelsLive returns models with active field", async () => {
		const apiKey = Bun.env.GROQ_API_KEY!;
		const models = await listGroqModelsLive(apiKey);
		expect(models.object).toBe("list");
		expect(models.data.length).toBeGreaterThan(0);
		for (const m of models.data) {
			expect(typeof m.id).toBe("string");
			expect(typeof m.active).toBe("boolean");
		}
	});

	test("deprecated models are marked active: false in fallback", async () => {
		const models = await listGroqModelsLive("fake-key-for-fallback");
		const deprecatedIds = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "groq/compound-mini"];
		for (const id of deprecatedIds) {
			const model = models.data.find(m => m.id === id);
			if (model) {
				expect(model.active).toBe(false);
			}
		}
	});
});
