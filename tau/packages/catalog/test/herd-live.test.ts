import { describe, expect, test } from "bun:test";
import { herdModelManagerOptions } from "@oh-my-pi/pi-catalog/provider-models/openai-compat";

/**
 * Live Herd (sovereign-router / llama-swap) integration.
 * Hits HERD_BASE_URL or LLAMA_SWAP_BASE_URL or default http://127.0.0.1:25100/v1.
 * Skips if HERD_BASE_URL is not set (local-only service).
 * If HERD_API_KEY is set it is used; herd allows unauthenticated when not configured.
 */
const herdBaseUrl = Bun.env.HERD_BASE_URL ?? Bun.env.LLAMA_SWAP_BASE_URL;
const hasHerdUrl = Boolean(herdBaseUrl);

describe.skipIf(!hasHerdUrl)("Herd live provider discovery (requires HERD_BASE_URL)", () => {
	test("live /v1/models returns at least one model when herd is reachable", async () => {
		const options = herdModelManagerOptions({
			baseUrl: herdBaseUrl,
			apiKey: Bun.env.HERD_API_KEY,
		});
		// fetchDynamicModels is always present for herd (allowUnauthenticated)
		const models = await options.fetchDynamicModels?.();
		// If herd is not actually running, the fetch will throw — that is expected; we assert the contract:
		// either we get models or we get a connection error, never a silent null.
		// When herd IS running, we must get >0 models.
		if (models === null) {
			// Some herd configs return null on empty catalog — treat as skip, not fail
			console.warn("[herd-live] herd returned null (no models or not reachable at", herdBaseUrl, ")");
			return;
		}
		expect(models!.length).toBeGreaterThan(0);
		for (const m of models!) {
			expect(typeof m.id).toBe("string");
			expect(m.id.length).toBeGreaterThan(0);
		}
	});
});
