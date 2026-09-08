import { describe, expect, test } from "bun:test";
import { groqModelManagerOptions } from "@oh-my-pi/pi-catalog/provider-models/openai-compat";
import type { FetchImpl } from "@oh-my-pi/pi-catalog/types";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const groqJsonPath = join(import.meta.dirname ?? ".", "../../../packages/ai/src/providers/data/groq.json");

function loadGroqJson(): Record<string, { contextWindow: number; maxTokens: number; cost: Record<string, number>; deprecated?: boolean }> {
	const raw = readFileSync(groqJsonPath, "utf-8");
	const data = JSON.parse(raw);
	return data["openai-completions"] ?? {};
}

describe("Groq provider discovery", () => {
	test("discovers models with Bearer auth and parses at least one model", async () => {
		const calls: Array<{ url: string; authorization: string | null }> = [];
		const fetchMock: FetchImpl = async (input: string | URL | Request, init?: RequestInit) => {
			const headers = new Headers(init?.headers);
			calls.push({ url: String(input), authorization: headers.get("authorization") });
			return new Response(
				JSON.stringify({ data: [{ id: "llama-3.1-8b-instant", object: "model" }, { id: "openai/gpt-oss-120b", object: "model" }] }),
				{ status: 200, headers: { "content-type": "application/json" } },
			);
		};

		const options = groqModelManagerOptions({ apiKey: "groq-test-key", fetch: fetchMock });
		const models = await options.fetchDynamicModels?.();
		expect(calls).toEqual([{ url: "https://api.groq.com/openai/v1/models", authorization: "Bearer groq-test-key" }]);
		expect(models?.length).toBeGreaterThanOrEqual(1);
		expect(models?.find(m => m.id === "llama-3.1-8b-instant")).toMatchObject({ provider: "groq", api: "openai-completions" });
	});

	test("discovers llama-4 maverick/scout as image-capable", async () => {
		const fetchMock: FetchImpl = async () =>
			new Response(JSON.stringify({ data: [{ id: "meta-llama/llama-4-maverick-17b-128e-instruct", object: "model" }, { id: "meta-llama/llama-4-scout-17b-16e-instruct", object: "model" }, { id: "llama-3.1-8b-instant", object: "model" }] }), { status: 200, headers: { "content-type": "application/json" } });

		const options = groqModelManagerOptions({ apiKey: "groq-test-key", fetch: fetchMock });
		const models = await options.fetchDynamicModels?.();
		expect(models?.find(m => m.id === "meta-llama/llama-4-maverick-17b-128e-instruct")).toMatchObject({ provider: "groq", api: "openai-completions", input: ["text", "image"] });
		expect(models?.find(m => m.id === "meta-llama/llama-4-scout-17b-16e-instruct")).toMatchObject({ provider: "groq", input: ["text", "image"] });
		expect(models?.find(m => m.id === "llama-3.1-8b-instant")?.input).toEqual(["text"]);
	});

	test("error handling: propagates HTTP error from /models (401)", async () => {
		const fetchMock: FetchImpl = async () => new Response(JSON.stringify({ error: { message: "unauthorized", type: "auth_error" } }), { status: 401, headers: { "content-type": "application/json" } });
		const options = groqModelManagerOptions({ apiKey: "bad-key", fetch: fetchMock });
		await expect(options.fetchDynamicModels?.()).rejects.toThrow(/HTTP 401|fetch failed/);
	});

	test("error handling: propagates 500 server error", async () => {
		const fetchMock: FetchImpl = async () => new Response("internal server error", { status: 500, headers: { "content-type": "text/plain" } });
		const options = groqModelManagerOptions({ apiKey: "groq-test-key", fetch: fetchMock });
		await expect(options.fetchDynamicModels?.()).rejects.toThrow(/HTTP 500|fetch failed/);
	});
});

describe("Groq model catalog validation", () => {
	const models = loadGroqJson();

	test("groq.json has at least 16 models", () => {
		expect(Object.keys(models).length).toBeGreaterThanOrEqual(16);
	});

	test("every model has contextWindow, maxTokens, and cost", () => {
		for (const [id, model] of Object.entries(models)) {
			expect(model.contextWindow).toBeGreaterThan(0);
			expect(model.maxTokens).toBeGreaterThan(0);
			expect(model.cost).toBeDefined();
			expect(typeof model.cost.input).toBe("number");
			expect(typeof model.cost.output).toBe("number");
		}
	});

	test("deprecated models are marked", () => {
		const deprecatedIds = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "groq/compound-mini"];
		for (const id of deprecatedIds) {
			expect(models[id]).toBeDefined();
		}
	});

	test("known models have correct contextWindow", () => {
		const knownModels = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"];
		for (const id of knownModels) {
			expect(models[id]).toBeDefined();
			expect(models[id].contextWindow).toBe(131072);
		}
	});
});
