import { createApiKeyLogin } from "./api-key-login";
import type { OAuthLoginCallbacks } from "./oauth/types";
import type { ProviderDefinition } from "./types";

const PROVIDER_ID = "herd";
export const DEFAULT_LOCAL_TOKEN = "herd-local";

export const loginHerd = createApiKeyLogin({
	providerLabel: PROVIDER_ID,
	promptMessage: "Optional: Paste Herd API key (to customize endpoint URL, set HERD_BASE_URL env var)",
	placeholder: DEFAULT_LOCAL_TOKEN,
	validation: null,
	emptyKeyFallback: DEFAULT_LOCAL_TOKEN,
});

export const herdProvider = {
	id: "herd",
	name: "Herd (Local OpenAI-compatible)",
	login: (cb: OAuthLoginCallbacks) => loginHerd(cb),
} as const satisfies ProviderDefinition;
