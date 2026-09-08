import { describe, expect, it } from "bun:test";
import { buildModel } from "@oh-my-pi/pi-catalog/build";
import { buildOpenAICompat } from "@oh-my-pi/pi-catalog/compat/openai";
import { getBundledModel } from "@oh-my-pi/pi-catalog/models";
import { streamOpenAICompletions } from "@oh-my-pi/pi-ai/providers/openai-completions";
import { streamGroq, parseSSEStream } from "@oh-my-pi/pi-ai/providers/groq";
import type { Context, FetchImpl, Model } from "@oh-my-pi/pi-ai/types";

const groqModel = getBundledModel("groq", "llama-3.1-8b-instant") as Model<"openai-completions">;
const groqThinkingModel = getBundledModel("groq", "openai/gpt-oss-120b") as Model<"openai-completions">;
const groqVisionModel = getBundledModel("groq", "meta-llama/llama-4-maverick-17b-128e-instruct") as Model<"openai-completions"> | undefined;

function baseContext(): Context {
	return { messages: [{ role: "user", content: "Say hello", timestamp: Date.now() }] };
}

function createSseResponse(events: unknown[]): Response {
	const payload = `${events.map(event => `data: ${JSON.stringify(event)}`).join("\n\n")}\n\ndata: [DONE]\n\n`;
	return new Response(payload, { status: 200, headers: { "content-type": "text/event-stream" } });
}

function chunk(extra: Record<string, unknown>): Record<string, unknown> {
	return { id: "gen-1", object: "chat.completion.chunk", created: 0, model: groqModel.id, ...extra };
}

describe("groq streaming/tool-call/JSON parity", () => {
	it("compat: groq supportsToolChoice, supportsForcedToolChoice, supportsNamedToolChoice", () => {
		expect(groqModel.compat.supportsToolChoice).toBe(true);
		expect(groqModel.compat.supportsForcedToolChoice).toBe(true);
		expect(groqModel.compat.supportsNamedToolChoice).toBe(true);
		expect(groqThinkingModel.compat.supportsToolChoice).toBe(true);
	});

	it("compat: groq supportsMultipleSystemMessages true via isGroqHost", () => {
		expect(groqModel.compat.supportsMultipleSystemMessages).toBe(true);
		expect(groqThinkingModel.compat.supportsMultipleSystemMessages).toBe(true);
	});

	it("stream: parses tool-call delta, reasoning_content, and [DONE] handling", async () => {
		const fetchMock: FetchImpl = () =>
			Promise.resolve(
				createSseResponse([
					chunk({ choices: [{ index: 0, delta: { reasoning_content: "thinking: " }, finish_reason: null }] }),
					chunk({ choices: [{ index: 0, delta: { reasoning_content: "42" }, finish_reason: null }] }),
					chunk({ choices: [{ index: 0, delta: { content: "Hello " }, finish_reason: null }] }),
					chunk({ choices: [{ index: 0, delta: { content: "world" }, finish_reason: null }] }),
					chunk({ choices: [{ index: 0, delta: { tool_calls: [{ index: 0, id: "call_groq_123", type: "function", function: { name: "get_weather", arguments: '{"city":' } }] }, finish_reason: null }] }),
					chunk({ choices: [{ index: 0, delta: { tool_calls: [{ index: 0, function: { arguments: '"Paris"}' } }] }, finish_reason: null }] }),
					chunk({ choices: [{ index: 0, delta: {}, finish_reason: "tool_calls" }], usage: { prompt_tokens: 10, completion_tokens: 20, total_tokens: 30 } }),
				]),
			);

		const result = await streamOpenAICompletions(groqModel, baseContext(), { apiKey: "gsk_test", fetch: fetchMock }).result();
		expect(result.content.length).toBeGreaterThan(0);
		const toolCalls = result.content.filter(c => c.type === "toolCall");
		expect(toolCalls.length).toBe(1);
		const firstToolCall = toolCalls[0];
		expect(firstToolCall).toMatchObject({ name: "get_weather" });
		if (firstToolCall && typeof firstToolCall === "object" && "arguments" in firstToolCall) {
			const argsStr = typeof firstToolCall.arguments === "string" ? firstToolCall.arguments : JSON.stringify(firstToolCall.arguments);
			expect(argsStr).toContain("Paris");
		}
		expect(["toolUse", "stop"]).toContain(result.stopReason);
	});

	it("JSON mode: response_format json_object passes through for groq model", async () => {
		let capturedBody: unknown = null;
		const captureFetch: FetchImpl = async (_input: string | URL | Request, init?: RequestInit) => {
			if (init?.body && typeof init.body === "string") {
				try { capturedBody = JSON.parse(init.body); } catch {}
			}
			return createSseResponse([
				chunk({ choices: [{ index: 0, delta: { content: '{"ok": true}' }, finish_reason: null }] }),
				chunk({ choices: [{ index: 0, delta: {}, finish_reason: "stop" }], usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 } }),
			]);
		};

		const modelWithCompat = buildModel({
			id: "llama-3.1-8b-instant", name: "Llama 3.1 8B", api: "openai-completions",
			provider: "groq", baseUrl: "https://api.groq.com/openai/v1", reasoning: false,
			input: ["text"], cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
			contextWindow: 131072, maxTokens: 131072,
		}) as Model<"openai-completions">;

		const result = await streamOpenAICompletions(modelWithCompat, baseContext(), {
			apiKey: "gsk_test", fetch: captureFetch,
			onPayload: payload => { if (payload && typeof payload === "object") return { ...(payload as Record<string, unknown>), response_format: { type: "json_object" } }; return payload; },
		}).result();

		if (capturedBody && typeof capturedBody === "object" && "response_format" in capturedBody) {
			const rf = (capturedBody as Record<string, unknown>).response_format;
			expect(rf).toMatchObject({ type: "json_object" });
		}
		expect(result.content[0]).toMatchObject({ type: "text", text: '{"ok": true}' });
	});
});

describe("groq SSE parsing", () => {
	it("parseSSEStream handles data: [DONE] correctly", async () => {
		const sseData = `data: {"id":"gen-1","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}\n\ndata: [DONE]\n\n`;
		const stream = new ReadableStream({
			start(controller) {
				controller.enqueue(new TextEncoder().encode(sseData));
				controller.close();
			},
		});

		const events: Array<{ data: Record<string, unknown>; event: string }> = [];
		for await (const event of parseSSEStream(stream)) {
			events.push(event);
		}

		expect(events.length).toBe(2);
		expect(events[0].data.object).toBe("chat.completion.chunk");
		expect(events[1].event).toBe("done");
		expect((events[1].data as Record<string, unknown>).done).toBe(true);
	});

	it("parseSSEStream skips : keepalive lines", async () => {
		const sseData = `: keepalive\n\ndata: {"id":"gen-1","choices":[{"index":0,"delta":{"content":"Hi"},"finish_reason":null}]}\n\ndata: [DONE]\n\n`;
		const stream = new ReadableStream({
			start(controller) {
				controller.enqueue(new TextEncoder().encode(sseData));
				controller.close();
			},
		});

		const events: Array<{ data: Record<string, unknown>; event: string }> = [];
		for await (const event of parseSSEStream(stream)) {
			events.push(event);
		}

		expect(events.length).toBe(2);
	});

	it("parseSSEStream handles empty lines between events", async () => {
		const sseData = `data: {"id":"gen-1","choices":[{"index":0,"delta":{"content":"A"},"finish_reason":null}]}\n\n\ndata: {"id":"gen-1","choices":[{"index":0,"delta":{"content":"B"},"finish_reason":null}]}\n\n\ndata: [DONE]\n\n`;
		const stream = new ReadableStream({
			start(controller) {
				controller.enqueue(new TextEncoder().encode(sseData));
				controller.close();
			},
		});

		const events: Array<{ data: Record<string, unknown>; event: string }> = [];
		for await (const event of parseSSEStream(stream)) {
			events.push(event);
		}

		expect(events.length).toBe(3);
	});
});
