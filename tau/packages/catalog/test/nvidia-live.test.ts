import { describe, expect, test } from "bun:test";
import { nvidiaModelManagerOptions } from "@oh-my-pi/pi-catalog/provider-models/openai-compat";

/**
 * Live NVIDIA NIM integration: hits https://integrate.api.nvidia.com/v1/models with a real key.
 * Skips gracefully if neither NVIDIA_API_KEY nor NVIDIA_NIM_API_KEY is present.
 * Run: bun test packages/catalog/test/nvidia-live.test.ts
 */
const nvidiaKey = Bun.env.NVIDIA_API_KEY ?? Bun.env.NVIDIA_NIM_API_KEY;
const hasNvidiaKey = Boolean(nvidiaKey);

describe.skipIf(!hasNvidiaKey)("NVIDIA live provider discovery (requires NVIDIA_API_KEY)", () => {
	test("live /v1/models returns at least one model", async () => {
		const apiKey = nvidiaKey!;
		const options = nvidiaModelManagerOptions({ apiKey });
		const models = await options.fetchDynamicModels?.();
		expect(models).toBeDefined();
		expect(models!.length).toBeGreaterThan(0);
		for (const m of models!) {
			expect(m.provider).toBe("nvidia");
			expect(m.api).toBe("openai-completions");
			expect(typeof m.id).toBe("string");
			expect(m.id.length).toBeGreaterThan(0);
		}
	});

	test("live 401 check: NVIDIA /models is public so bad key still returns models (no 401)", async () => {
		const options = nvidiaModelManagerOptions({ apiKey: "bad-key-live-check" });
		const models = await options.fetchDynamicModels?.();
		// NVIDIA NIM does not gate /models on auth — even a bad key returns 200. Verify we get models, not a throw.
		expect(models).toBeDefined();
		expect(models!.length).toBeGreaterThan(0);
	});
});
