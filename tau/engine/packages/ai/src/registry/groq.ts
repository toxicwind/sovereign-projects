import { createApiKeyLogin } from "./api-key-login";
import type { OAuthLoginCallbacks } from "./oauth/types";
import type { ProviderDefinition } from "./types";
import { groqProvider, GROQ_BASE_URL, GROQ_AUTH_URL, streamGroq, streamSimpleGroq, listGroqModelsLive } from "../../providers/groq.ts";

export { streamGroq, streamSimpleGroq, listGroqModelsLive };

export const loginGroq = createApiKeyLogin({
	providerLabel: "Groq",
	authUrl: "https://console.groq.com/keys",
	instructions: "Copy your API key from Groq Console → API Keys",
	promptMessage: "Paste your Groq API key",
	placeholder: "gsk_...",
	validation: {
		kind: "chat-completions",
		provider: "Groq",
		baseUrl: "https://api.groq.com/openai/v1",
		model: "openai/gpt-oss-20b", // Non-deprecated model (was llama-3.1-8b-instant)
	},
});

export const groqProvider = {
	id: "groq",
	name: "Groq",
	login: (cb: OAuthLoginCallbacks) => loginGroq(cb),
	baseUrl: GROQ_BASE_URL,
	authUrl: GROQ_AUTH_URL,
	streamGroq,
	streamSimpleGroq,
	listGroqModelsLive,
} as const satisfies ProviderDefinition;
